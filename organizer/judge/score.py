"""Score a judged run: C1-C10 from proxy logs, worker results and golden labels (organizer only).

  python organizer/judge/score.py --run organizer/runs/baseline
  python organizer/judge/score.py --run organizer/runs/team-07 --baseline organizer/runs/baseline/report.json
"""
import argparse
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PRICES = yaml.safe_load((HERE / "prices.yaml").read_text())
REPLY_JUDGE_MODEL = "claude-sonnet-5-5"
FIELDS = ["category", "priority", "kb_article_id", "refund_eligible"]


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def tier(model):
    for name, prefixes in PRICES["model_tiers"].items():
        if any((model or "").startswith(p) for p in prefixes):
            return name
    return "other"


def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def percentile(values, q):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (k - lo), 2)


def normalise(field, value):
    if field == "refund_eligible":
        return str(value).strip().lower() == "true"
    if value is None or str(value).strip().lower() in ("", "null", "none"):
        return None
    if field == "kb_article_id":
        m = re.search(r"KB-\d{3}", str(value))
        return m.group(0) if m else None
    return str(value).strip().lower() if field == "category" else str(value).strip().upper()


def api_client():
    import anthropic
    kwargs = {"base_url": "https://api.anthropic.com"}
    if os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], **kwargs)
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    headers = {"anthropic-beta": "oauth-2025-04-20"} if token and token.startswith("sk-ant-oat") else None
    return anthropic.Anthropic(auth_token=token, default_headers=headers, **kwargs)


def oauth_system():
    """Claude Code OAuth tokens need the Claude Code identity system block on the Messages API."""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or ""
    if os.environ.get("ANTHROPIC_API_KEY") or not token.startswith("sk-ant-oat"):
        return {}
    return {"system": "You are Claude Code, Anthropic's official CLI for Claude."}


def judge_reply(client, repo, ticket, golden, reply):
    if not reply:
        return False, "empty reply"
    words = len(str(reply).split())
    if words > 130:
        return False, f"{words} words"
    article = ""
    if golden.get("kb_article_id"):
        text = (Path(repo) / "data" / "kb" / f"{golden['kb_article_id']}.md").read_text(encoding="utf-8")
        article = text.split("## Summary", 1)[-1].split("##", 1)[0].strip()
    prompt = (
        "You grade customer support replies for Nimbus Cloud. Pass the reply only if ALL hold:\n"
        "1. It addresses the customer's specific issue or message.\n"
        "2. If a reference resolution is given, the next step it gives is consistent with it (it need not be complete).\n"
        "3. It is polite and professional.\n"
        "4. It does not promise a refund when refund_eligible is false, and does not invent policies.\n\n"
        f"Ticket:\n{json.dumps(ticket, indent=2)}\n\nrefund_eligible: {golden['refund_eligible']}\n"
        f"Reference resolution: {article or '(none - feature request or general inquiry)'}\n\n"
        f"Reply under review:\n{reply}"
    )
    response = client.messages.create(
        model=REPLY_JUDGE_MODEL,
        max_tokens=1024,
        **oauth_system(),
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": {
            "type": "object",
            "properties": {"pass": {"type": "boolean"}, "reason": {"type": "string"}},
            "required": ["pass", "reason"], "additionalProperties": False}}},
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(next(b.text for b in response.content if b.type == "text"))
    return bool(data["pass"]), data["reason"]


def managed_costs(client, session_ids):
    out = {}
    for sid in session_ids:
        try:
            s = client.beta.sessions.retrieve(sid)
            usage = s.usage.model_dump() if getattr(s, "usage", None) else {}
            amount = ((usage.get("list_cost") or {}).get("amount")) or "0"
            out[sid] = {"usd": int(amount) / 100.0, "status": s.status,
                        "active_seconds": usage.get("active_seconds"), "archived": bool(getattr(s, "archived_at", None))}
        except Exception as e:  # noqa: BLE001
            out[sid] = {"usd": 0.0, "status": f"unknown ({type(e).__name__})"}
    return out


def score(args):
    run = Path(args.run)
    repo = Path(args.repo)
    golden = {g["ticket_id"]: g for g in read_jsonl(HERE / "golden.jsonl")}
    tickets = {t["ticket_id"]: t for t in read_jsonl(repo / "data" / "tickets.jsonl")}
    results = {}
    for p in sorted(run.glob("results_w*.jsonl")):
        for r in read_jsonl(p):
            results[r["ticket_id"]] = r
    entries = [e for p in sorted(run.glob("proxy_w*.jsonl")) for e in read_jsonl(p)]
    requests = [e for e in entries if e.get("event") == "request" and e.get("ticket_id")]
    rejected = [e for e in entries if e.get("event") == "rejected"]
    ids = sorted(results)
    n = len(ids) or 1

    per = defaultdict(lambda: defaultdict(float))
    seen_tools = defaultdict(Counter)
    model_calls = Counter()
    sessions_created, sessions_closed = {}, set()
    for e in requests:
        t = per[e["ticket_id"]]
        kind = e["kind"]
        t[f"req_{kind}"] += 1
        if kind in ("messages", "sdk_turn"):
            u = e.get("usage") or {}
            t["calls"] += 1
            t["cost"] += e.get("cost_usd") or 0
            t["in_uncached"] += u.get("input_tokens", 0)
            t["in_cache_write"] += u.get("cache_creation_input_tokens", 0)
            t["in_cache_read"] += u.get("cache_read_input_tokens", 0)
            t["out"] += u.get("output_tokens", 0)
            t["tool_results"] += e.get("tool_results", 0)
            t["tool_errors"] += e.get("tool_errors", 0)
            model_calls[tier(e.get("model"))] += 1
            for tu in e.get("tool_uses") or []:
                t["tool_calls"] += 1
                key = (tu["name"], tu["input_sha"])
                if seen_tools[e["ticket_id"]][key]:
                    t["dup_tool_calls"] += 1
                seen_tools[e["ticket_id"]][key] += 1
            if kind == "sdk_turn":
                t["turns"] += 1
        if e.get("session_id"):
            sessions_created[e["session_id"]] = e["ticket_id"]
        if e.get("session_closed"):
            sessions_closed.add(e["session_closed"])
        if kind == "managed_agent" and e.get("created_id"):
            t["agents_created"] += 1
        if kind == "managed_environment" and e.get("created_id"):
            t["environments_created"] += 1
        if kind == "files" and e["method"] == "POST":
            t["files_uploaded"] += 1
    for e in rejected:
        if e.get("ticket_id"):
            per[e["ticket_id"]][f"rejected_{e['reason']}"] += 1

    managed = {}
    if sessions_created and not args.skip_managed_costs:
        managed = managed_costs(api_client(), list(sessions_created))
        for sid, info in managed.items():
            per[sessions_created[sid]]["cost"] += info["usd"]
            per[sessions_created[sid]]["managed_cost"] += info["usd"]

    def avg(key):
        return round(sum(per[i][key] for i in ids) / n, 4)

    total_in = sum(per[i]["in_uncached"] + per[i]["in_cache_write"] + per[i]["in_cache_read"] for i in ids)
    latencies = [results[i]["latency_s"] for i in ids]
    tool_results = sum(per[i]["tool_results"] for i in ids)

    # C10 quality
    correct = Counter()
    reply_pass, reply_notes = 0, {}
    for i in ids:
        res = results[i].get("result") or {}
        for f in FIELDS:
            if normalise(f, res.get(f)) == normalise(f, golden[i].get(f)):
                correct[f] += 1
    if not args.skip_reply_judge:
        client = api_client()

        def grade(i):
            res = results[i].get("result") or {}
            try:
                return i, judge_reply(client, repo, tickets[i], golden[i], res.get("reply_draft"))
            except Exception as e:  # noqa: BLE001
                return i, (False, f"judge error: {e}")

        with ThreadPoolExecutor(max_workers=8) as pool:
            for i, (ok, why) in pool.map(grade, ids):
                reply_pass += ok
                reply_notes[i] = {"pass": ok, "reason": why}
    accuracy = {f: pct(correct[f], n) for f in FIELDS}
    accuracy["reply_pass"] = pct(reply_pass, n) if not args.skip_reply_judge else None
    parts = [v for v in accuracy.values() if v is not None]
    accuracy["overall"] = round(sum(parts) / len(parts), 2)

    total_calls = sum(model_calls.values()) or 1
    report = {
        "run": run.name, "tickets": len(ids),
        "C1_cost_usd_per_ticket": avg("cost"),
        "C1_managed_cost_usd_per_ticket": avg("managed_cost"),
        "C2_input_tokens_per_ticket": {"uncached": avg("in_uncached"), "cache_write": avg("in_cache_write"),
                                       "cache_read": avg("in_cache_read")},
        "C3_output_tokens_per_ticket": avg("out"),
        "C4_cache_read_pct": pct(sum(per[i]["in_cache_read"] for i in ids), total_in),
        "C5_model_mix_pct": {k: pct(v, total_calls) for k, v in model_calls.items()},
        "C6_llm_calls_per_ticket": avg("calls"),
        "C7_agent_turns_per_ticket": avg("turns"),
        "C7_cap_hits": sum(1 for i in ids if per[i]["rejected_ticket_cap"] or results[i].get("timed_out")),
        "C8_tool_calls_per_ticket": avg("tool_calls"),
        "C8_tool_error_rate_pct": pct(sum(per[i]["tool_errors"] for i in ids), tool_results),
        "C8_duplicate_tool_calls_per_ticket": avg("dup_tool_calls"),
        "C9_latency_s": {"p50": percentile(latencies, 0.5), "p95": percentile(latencies, 0.95)},
        "C10_accuracy_pct": accuracy,
        "managed": {
            "agents_created_per_ticket": avg("agents_created"),
            "environments_created_per_ticket": avg("environments_created"),
            "sessions_created": len(sessions_created),
            "sessions_left_open": sum(1 for s in sessions_created if s not in sessions_closed
                                      and not managed.get(s, {}).get("archived")),
            "session_api_requests_per_ticket": avg("req_managed_session"),
            "files_uploaded_per_ticket": avg("files_uploaded"),
        },
        "errors": {i: results[i]["error"] for i in ids if results[i].get("error")},
        "budget_rejections": sum(1 for e in rejected if e["reason"] == "budget"),
    }
    if args.baseline:
        report["points"] = points(report, json.loads(Path(args.baseline).read_text()))
    (run / "report.json").write_text(json.dumps(report, indent=2))
    (run / "reply_judge.json").write_text(json.dumps(reply_notes, indent=2))
    print(json.dumps(report, indent=2))


def reduction(new, old):
    return max(0.0, (old - new) / old) if old else 0.0


def points(r, b):
    """Measured part of the rubric (55 points). Judges award the other 45."""
    gate = r["C10_accuracy_pct"]["overall"] >= b["C10_accuracy_pct"]["overall"] - 2
    if not gate:
        return {"quality_gate": False, "measured_total": 0}
    c1 = 25 * min(1.0, reduction(r["C1_cost_usd_per_ticket"], b["C1_cost_usd_per_ticket"]) / 0.85)
    unc = reduction(r["C2_input_tokens_per_ticket"]["uncached"], b["C2_input_tokens_per_ticket"]["uncached"])
    out = reduction(r["C3_output_tokens_per_ticket"], b["C3_output_tokens_per_ticket"])
    cache = min(1.0, r["C4_cache_read_pct"] / 50.0)
    c234 = round(4 * unc + 3 * out + 3 * cache, 2)
    calls = reduction(r["C6_llm_calls_per_ticket"], b["C6_llm_calls_per_ticket"])
    turns = reduction(r["C7_agent_turns_per_ticket"], b["C7_agent_turns_per_ticket"]) \
        if b["C7_agent_turns_per_ticket"] else 1.0
    no_caps = 1.0 if r["C7_cap_hits"] == 0 else 0.0
    tool_err = 1.0 if r["C8_tool_error_rate_pct"] < 5 else 0.0
    c678 = round(4 * calls + 3 * turns + 1.5 * no_caps + 1.5 * tool_err, 2)
    c9 = round(5 * min(1.0, reduction(r["C9_latency_s"]["p95"], b["C9_latency_s"]["p95"]) / 0.85), 2)
    mix = r["C5_model_mix_pct"]
    c5 = round(5 * min(1.0, (mix.get("haiku", 0) + 0.5 * mix.get("sonnet", 0)) / 60.0), 2)
    total = round(c1 + c234 + c678 + c9 + c5, 2)
    return {"quality_gate": True, "C1": round(c1, 2), "C2_C4": c234, "C6_C8": c678, "C9": c9, "C5": c5,
            "measured_total": total}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--repo", default=str(HERE.parent.parent))
    ap.add_argument("--baseline")
    ap.add_argument("--skip-reply-judge", action="store_true")
    ap.add_argument("--skip-managed-costs", action="store_true")
    score(ap.parse_args())
