"""Judged run of a team repo (organizer only).

Starts one proxy per worker so every API request is attributed to the ticket that
worker is processing, runs the tickets, then scores the run.

  python organizer/judge/run_judged.py --name baseline --repo . --sample 40 --workers 4 --budget-usd 400
  python organizer/judge/run_judged.py --name team-07 --repo ../team-07 --sample 40 --workers 4 \
      --baseline organizer/runs/baseline/report.json

The team repo must expose app.pipeline.process_ticket(ticket) -> dict (async or sync).
Credentials come from this process's environment (ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN /
CLAUDE_CODE_OAUTH_TOKEN). ANTHROPIC_BASE_URL is overridden to point at the proxy.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"


def select_tickets(repo, sample):
    with open(Path(repo) / "data" / "tickets.jsonl", encoding="utf-8") as f:
        ids = [json.loads(line)["ticket_id"] for line in f if line.strip()]
    if not sample or sample >= len(ids):
        return ids
    step = len(ids) / sample
    return [ids[int(i * step)] for i in range(sample)]


def wait_for_proxy(port, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/__judge/stats", timeout=2).read()
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"proxy on port {port} did not start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--repo", default=str(HERE.parent.parent))
    ap.add_argument("--sample", type=int, default=40, help="0 = all 200 tickets")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=1800, help="seconds per ticket")
    ap.add_argument("--budget-usd", type=float, default=0, help="per-worker hard stop, 0 = none")
    ap.add_argument("--max-requests-per-ticket", type=int, default=150)
    ap.add_argument("--base-port", type=int, default=8787)
    ap.add_argument("--baseline", help="baseline report.json to score improvements against")
    ap.add_argument("--skip-reply-judge", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    repo = str(Path(args.repo).resolve())
    run_dir = RUNS / args.name
    run_dir.mkdir(parents=True, exist_ok=True)
    tickets = select_tickets(repo, args.sample)
    slices = [tickets[i :: args.workers] for i in range(args.workers)]
    (run_dir / "tickets.json").write_text(json.dumps(tickets))

    proxies, workers = [], []
    try:
        for i, chunk in enumerate(slices):
            if not chunk:
                continue
            port = args.base_port + i
            log = run_dir / f"proxy_w{i}.jsonl"
            if log.exists():
                log.unlink()
            proxies.append(subprocess.Popen(
                [sys.executable, str(HERE / "proxy.py"), "--port", str(port), "--log", str(log),
                 "--budget-usd", str(args.budget_usd), "--max-requests-per-ticket", str(args.max_requests_per_ticket)],
                stdout=subprocess.DEVNULL, stderr=open(run_dir / f"proxy_w{i}.err", "w"),
            ))
            wait_for_proxy(port)
            env = dict(os.environ)
            env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port}"
            env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
            cmd = [sys.executable, str(HERE / "worker.py"), "--repo", repo, "--port", str(port),
                   "--tickets", ",".join(chunk), "--out", str(run_dir / f"results_w{i}.jsonl"),
                   "--timeout", str(args.timeout), "--name", f"w{i}"]
            if args.verbose:
                cmd.append("--verbose")
            workers.append(subprocess.Popen(cmd, env=env, cwd=repo))
        for w in workers:
            w.wait()
    finally:
        for p in proxies:
            p.terminate()

    score_cmd = [sys.executable, str(HERE / "score.py"), "--run", str(run_dir), "--repo", repo]
    if args.baseline:
        score_cmd += ["--baseline", args.baseline]
    if args.skip_reply_judge:
        score_cmd.append("--skip-reply-judge")
    subprocess.run(score_cmd, check=False)


if __name__ == "__main__":
    main()
