"""Run a slice of tickets through a team's app.pipeline.process_ticket (spawned by run_judged.py)."""
import argparse
import asyncio
import inspect
import json
import os
import sys
import time
import traceback
import urllib.request


def tell_proxy(port, ticket_id):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/__judge/ticket",
        data=json.dumps({"ticket_id": ticket_id}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=10).read()


async def main(args):
    sys.path.insert(0, args.repo)
    os.chdir(args.repo)
    from app.pipeline import process_ticket  # team code

    wanted = set(args.tickets.split(","))
    with open(os.path.join(args.repo, "data", "tickets.jsonl"), encoding="utf-8") as f:
        tickets = [json.loads(line) for line in f if line.strip()]
    tickets = [t for t in tickets if t["ticket_id"] in wanted]

    with open(args.out, "w", encoding="utf-8") as out:
        for ticket in tickets:
            tell_proxy(args.port, ticket["ticket_id"])
            started = time.time()
            record = {"ticket_id": ticket["ticket_id"], "result": None, "error": None, "timed_out": False}
            try:
                if inspect.iscoroutinefunction(process_ticket):
                    coro = process_ticket(ticket)
                else:
                    coro = asyncio.to_thread(process_ticket, ticket)
                record["result"] = await asyncio.wait_for(coro, timeout=args.timeout)
            except asyncio.TimeoutError:
                record["timed_out"] = True
                record["error"] = "timeout"
            except BaseException as e:  # noqa: BLE001 - judge must keep going
                record["error"] = f"{type(e).__name__}: {e}"[:500]
                if args.verbose:
                    traceback.print_exc()
            record["latency_s"] = round(time.time() - started, 2)
            out.write(json.dumps(record, default=str) + "\n")
            out.flush()
            print(f"[{args.name}] {ticket['ticket_id']} {record['latency_s']}s "
                  f"{'ERR ' + record['error'] if record['error'] else 'ok'}", flush=True)
    tell_proxy(args.port, None)
    os._exit(0)  # don't wait on team background tasks / SDK subprocesses


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--name", default="w0")
    ap.add_argument("--verbose", action="store_true")
    asyncio.run(main(ap.parse_args()))
