"""Judge proxy: forwards every Anthropic API request and records usage (organizer only).

Teams' code reaches the API only through this proxy (ANTHROPIC_BASE_URL). It:
  - logs one JSON line per request to --log (model, usage, tool calls, tool errors, timing)
  - attributes each request to the ticket set via POST /__judge/ticket
  - refuses requests once the run exceeds --budget-usd
  - refuses model requests beyond --max-requests-per-ticket for the current ticket

  python organizer/judge/proxy.py --port 8787 --log organizer/runs/baseline/proxy.jsonl --budget-usd 500
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import yaml
from aiohttp import ClientSession, ClientTimeout, TCPConnector, ThreadedResolver, web

HERE = Path(__file__).resolve().parent
PRICES = yaml.safe_load((HERE / "prices.yaml").read_text())

HOP_HEADERS = {"host", "content-length", "transfer-encoding", "connection", "accept-encoding"}


def price_for(model):
    for key, value in PRICES["models"].items():
        if model and model.startswith(key):
            return value
    return PRICES["models"][PRICES["default_model"]]


def usage_cost(model, usage):
    p = price_for(model)
    return (
        usage.get("input_tokens", 0) * p["input"]
        + usage.get("cache_creation_input_tokens", 0) * p["cache_write"]
        + usage.get("cache_read_input_tokens", 0) * p["cache_read"]
        + usage.get("output_tokens", 0) * p["output"]
    ) / 1_000_000


def classify(path, user_agent):
    if path.startswith("/v1/messages/count_tokens"):
        return "count_tokens"
    if path.startswith("/v1/messages/batches"):
        return "batch"
    if path.startswith("/v1/messages"):
        return "sdk_turn" if "claude-cli" in (user_agent or "").lower() else "messages"
    for prefix, kind in (("/v1/sessions", "managed_session"), ("/v1/agents", "managed_agent"),
                         ("/v1/environments", "managed_environment"), ("/v1/files", "files")):
        if path.startswith(prefix):
            return kind
    return "other"


def tool_results_in_request(body):
    """Count tool_result blocks in the newest user turn and how many were errors."""
    try:
        messages = body.get("messages") or []
        last = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        if not last or not isinstance(last.get("content"), list):
            return 0, 0
        results = [b for b in last["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]
        errors = 0
        for r in results:
            content = r.get("content")
            text = content if isinstance(content, str) else json.dumps(content)
            if r.get("is_error") or text.strip().strip('"') in ("Error", '[{"type": "text", "text": "Error"}]') \
                    or '"text": "Error"}' in text:
                errors += 1
        return len(results), errors
    except Exception:
        return 0, 0


def parse_sse(raw):
    usage, model, tool_uses = {}, None, []
    current = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.startswith("data:"):
            continue
        try:
            event = json.loads(line[5:].strip())
        except ValueError:
            continue
        etype = event.get("type")
        if etype == "message_start":
            msg = event.get("message", {})
            model = msg.get("model")
            usage.update({k: v for k, v in (msg.get("usage") or {}).items() if isinstance(v, int)})
        elif etype == "message_delta":
            usage.update({k: v for k, v in (event.get("usage") or {}).items() if isinstance(v, int)})
        elif etype == "content_block_start" and event.get("content_block", {}).get("type") == "tool_use":
            block = event["content_block"]
            current[event.get("index")] = {"name": block.get("name"), "input": ""}
        elif etype == "content_block_delta" and event.get("delta", {}).get("type") == "input_json_delta":
            if event.get("index") in current:
                current[event["index"]]["input"] += event["delta"].get("partial_json", "")
        elif etype == "content_block_stop" and event.get("index") in current:
            tool_uses.append(current.pop(event["index"]))
    return usage, model, tool_uses


def parse_json_response(raw):
    try:
        data = json.loads(raw)
    except ValueError:
        return {}, None, [], {}
    usage = {k: v for k, v in (data.get("usage") or {}).items() if isinstance(v, int)}
    tool_uses = [{"name": b.get("name"), "input": json.dumps(b.get("input"), sort_keys=True)}
                 for b in data.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
    return usage, data.get("model"), tool_uses, data


class Judge:
    def __init__(self, args):
        self.upstream = args.upstream.rstrip("/")
        self.log_path = Path(args.log)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.budget = args.budget_usd
        self.max_per_ticket = args.max_requests_per_ticket
        self.ticket = None
        self.ticket_requests = {}
        self.total_cost = 0.0
        self.session = None

    def write(self, entry):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    async def set_ticket(self, request):
        data = await request.json()
        self.ticket = data.get("ticket_id")
        self.write({"event": "ticket", "ticket_id": self.ticket, "ts": time.time()})
        return web.json_response({"ok": True, "ticket_id": self.ticket})

    async def stats(self, request):
        return web.json_response({"total_cost_usd": self.total_cost, "ticket": self.ticket})

    def reject(self, status, message):
        return web.json_response({"type": "error", "error": {"type": "permission_error", "message": message}},
                                 status=status)

    async def forward(self, request):
        path = request.path
        body_bytes = await request.read()
        ua = request.headers.get("user-agent", "")
        kind = classify(path, ua)
        is_model_call = kind in ("messages", "sdk_turn")
        ticket = self.ticket

        if self.budget and self.total_cost >= self.budget:
            self.write({"event": "rejected", "reason": "budget", "ticket_id": ticket, "path": path, "ts": time.time()})
            return self.reject(403, f"Judge budget of ${self.budget} exhausted for this run.")
        if is_model_call and request.method == "POST":
            count = self.ticket_requests.get(ticket, 0) + 1
            self.ticket_requests[ticket] = count
            if self.max_per_ticket and count > self.max_per_ticket:
                self.write({"event": "rejected", "reason": "ticket_cap", "ticket_id": ticket, "path": path,
                            "ts": time.time()})
                return self.reject(403, f"Judge cap: more than {self.max_per_ticket} model requests for this ticket.")

        req_body = {}
        if body_bytes and "json" in request.headers.get("content-type", ""):
            try:
                req_body = json.loads(body_bytes)
            except ValueError:
                req_body = {}

        headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_HEADERS}
        url = self.upstream + path + (("?" + request.query_string) if request.query_string else "")
        started = time.time()
        async with self.session.request(request.method, url, headers=headers, data=body_bytes or None) as upstream:
            content_type = upstream.headers.get("content-type", "")
            resp_headers = {k: v for k, v in upstream.headers.items()
                            if k.lower() not in HOP_HEADERS and k.lower() != "content-encoding"}
            if "event-stream" in content_type:
                response = web.StreamResponse(status=upstream.status, headers=resp_headers)
                await response.prepare(request)
                chunks = []
                async for chunk in upstream.content.iter_any():
                    chunks.append(chunk)
                    await response.write(chunk)
                await response.write_eof()
                raw = b"".join(chunks)
                if path.startswith("/v1/messages"):
                    usage, model, tool_uses = parse_sse(raw)
                else:
                    usage, model, tool_uses = {}, None, []
                resp_json = {}
            else:
                raw = await upstream.read()
                response = web.Response(status=upstream.status, body=raw, headers=resp_headers)
                usage, model, tool_uses, resp_json = parse_json_response(raw)
            status = upstream.status

        model = model or req_body.get("model")
        cost = usage_cost(model, usage) if is_model_call and usage else 0.0
        self.total_cost += cost
        n_results, n_errors = tool_results_in_request(req_body) if is_model_call else (0, 0)
        entry = {
            "event": "request", "ts": started, "duration_s": round(time.time() - started, 3),
            "ticket_id": ticket, "kind": kind, "method": request.method, "path": path, "status": status,
            "model": model if is_model_call else None, "stream": "event-stream" in content_type,
            "usage": usage, "cost_usd": cost,
            "max_tokens": req_body.get("max_tokens"), "thinking": req_body.get("thinking"),
            "effort": (req_body.get("output_config") or {}).get("effort"),
            "n_tools_defined": len(req_body.get("tools") or []),
            "n_messages": len(req_body.get("messages") or []),
            "has_cache_control": "cache_control" in body_bytes.decode("utf-8", "replace") if is_model_call else None,
            "system_sha": hashlib.sha1(json.dumps(req_body.get("system"), sort_keys=True).encode()).hexdigest()[:12]
            if is_model_call else None,
            "tool_uses": [{"name": t["name"], "input_sha": hashlib.sha1(t["input"].encode()).hexdigest()[:12]}
                          for t in tool_uses],
            "tool_results": n_results, "tool_errors": n_errors,
        }
        if kind == "managed_session" and request.method == "POST" and path == "/v1/sessions":
            entry["session_id"] = resp_json.get("id")
        if kind in ("managed_agent", "managed_environment") and request.method == "POST":
            entry["created_id"] = resp_json.get("id")
        if kind == "managed_session" and (request.method == "DELETE" or path.endswith("/archive")):
            entry["session_closed"] = path.split("/")[3] if len(path.split("/")) > 3 else None
        self.write(entry)
        return response


async def make_app(args):
    judge = Judge(args)

    async def on_startup(app):
        judge.session = ClientSession(connector=TCPConnector(resolver=ThreadedResolver()), timeout=ClientTimeout(total=None, sock_read=900), auto_decompress=True)

    async def on_cleanup(app):
        await judge.session.close()

    app = web.Application(client_max_size=256 * 1024 * 1024)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_post("/__judge/ticket", judge.set_ticket)
    app.router.add_get("/__judge/stats", judge.stats)
    app.router.add_route("*", "/{tail:.*}", judge.forward)
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--upstream", default="https://api.anthropic.com")
    ap.add_argument("--log", required=True)
    ap.add_argument("--budget-usd", type=float, default=0, help="0 disables the run budget")
    ap.add_argument("--max-requests-per-ticket", type=int, default=150)
    args = ap.parse_args()
    web.run_app(make_app(args), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
