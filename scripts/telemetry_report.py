"""Summarise telemetry: per-run, per-step and per-ticket cost, tokens, calls and latency.

  python scripts/telemetry_report.py                      # every file in out/telemetry/
  python scripts/telemetry_report.py --last               # only the most recent run file
  python scripts/telemetry_report.py out/telemetry/<run_id>.jsonl
  python scripts/telemetry_report.py --html out/report.html
  python scripts/telemetry_report.py --compare before.json    # before/after table (a --json summary)
"""
import argparse
import html
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def load(path, last=False):
    path = Path(path)
    files = sorted(path.glob("*.jsonl")) if path.is_dir() else [path]
    if last:
        files = files[-1:]
    return [json.loads(line) for f in files for line in open(f, encoding="utf-8") if line.strip()]


def pct(values, q):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def tier(model):
    for name in ("opus", "sonnet", "haiku", "fable"):
        if name in (model or ""):
            return name
    return "other"


def summarise(records):
    calls = [r for r in records if r["type"] in ("llm_call", "agent_run")]
    tickets = [r for r in records if r["type"] == "ticket"]
    tools = [r for r in records if r["type"] == "tool_call"]
    n = len({r["ticket_id"] for r in tickets}) or 1
    tok = {k: sum(c.get(k, 0) for c in calls) for k in TOKEN_KEYS}
    total_in = tok["input_tokens"] + tok["cache_creation_input_tokens"] + tok["cache_read_input_tokens"]
    latencies = [t["latency_s"] for t in tickets]
    mix = Counter(tier(c["model"]) for c in calls)
    return {
        "tickets": len(tickets),
        "failed_tickets": sum(1 for t in tickets if t["status"] != "ok"),
        "cost_usd_total": sum(c["cost_usd"] for c in calls),
        "cost_usd_per_ticket": sum(c["cost_usd"] for c in calls) / n,
        "calls_per_ticket": len(calls) / n,
        "turns_per_ticket": sum(c.get("turns") or 0 for c in calls) / n,
        "tool_calls_per_ticket": len(tools) / n,
        "tool_error_pct": 100 * sum(1 for t in tools if not t["ok"]) / (len(tools) or 1),
        "uncached_in_per_ticket": tok["input_tokens"] / n,
        "cache_write_per_ticket": tok["cache_creation_input_tokens"] / n,
        "cache_read_per_ticket": tok["cache_read_input_tokens"] / n,
        "output_per_ticket": tok["output_tokens"] / n,
        "cache_read_pct": 100 * tok["cache_read_input_tokens"] / (total_in or 1),
        "model_mix_pct": {k: round(100 * v / (len(calls) or 1), 1) for k, v in mix.items()},
        "latency_p50_s": pct(latencies, 0.5),
        "latency_p95_s": pct(latencies, 0.95),
    }


def by_step(records):
    steps = defaultdict(lambda: {"calls": 0, "cost": 0.0, "in": 0, "cache_read": 0, "out": 0, "latency": []})
    for r in records:
        if r["type"] in ("llm_call", "agent_run"):
            s = steps[r["step"]]
            s["calls"] += 1
            s["cost"] += r["cost_usd"]
            s["in"] += r.get("input_tokens", 0) + r.get("cache_creation_input_tokens", 0)
            s["cache_read"] += r.get("cache_read_input_tokens", 0)
            s["out"] += r.get("output_tokens", 0)
        elif r["type"] == "step":
            steps[r["step"]]["latency"].append(r["latency_s"])
    rows = []
    for name, s in steps.items():
        rows.append([name, s["calls"], f"${s['cost']:.4f}", s["in"], s["cache_read"], s["out"],
                     f"{statistics.mean(s['latency']):.3f}" if s["latency"] else "-",
                     f"{pct(s['latency'], 0.95):.3f}" if s["latency"] else "-"])
    return ["step", "calls", "cost", "in (uncached+write)", "cache read", "out", "avg s", "p95 s"], rows


def by_ticket(records, top=10):
    per = defaultdict(lambda: {"cost": 0.0, "calls": 0, "out": 0, "latency": 0.0, "status": ""})
    for r in records:
        if r["type"] in ("llm_call", "agent_run"):
            per[r["ticket_id"]]["cost"] += r["cost_usd"]
            per[r["ticket_id"]]["calls"] += 1
            per[r["ticket_id"]]["out"] += r.get("output_tokens", 0)
        elif r["type"] == "ticket":
            per[r["ticket_id"]]["latency"] = r["latency_s"]
            per[r["ticket_id"]]["status"] = r["status"]
    worst = sorted(per.items(), key=lambda kv: -kv[1]["cost"])[:top]
    return ["ticket", "cost", "calls", "out tokens", "latency s", "status"], [
        [t, f"${v['cost']:.5f}", v["calls"], v["out"], f"{v['latency']:.2f}", v["status"]] for t, v in worst]


def table(header, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)] if rows else [len(h) for h in header]
    line = lambda cells: "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))  # noqa: E731
    return "\n".join([line(header), line(["-" * w for w in widths])] + [line(r) for r in rows])


def fmt(v):
    return f"{v:.5f}" if isinstance(v, float) and v < 1 else (f"{v:.2f}" if isinstance(v, float) else v)


def compare(before, after):
    rows = []
    for key in after:
        b, a = before.get(key), after[key]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            change = f"{100 * (a - b) / b:+.1f}%" if b else "-"
            rows.append([key, fmt(b), fmt(a), change])
        else:
            rows.append([key, b, a, ""])
    return ["metric", "before", "after", "change"], rows


def write_html(path, summary, step_table, ticket_table, cmp_table=None):
    def tbl(header, rows):
        head = "".join(f"<th>{html.escape(str(h))}</th>" for h in header)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    cards = "".join(
        f"<div class='card'><div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(fmt(v)))}</div></div>"
        for k, v in summary.items())
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>TicketPilot telemetry</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#fff;--fg:#1b1b1f;--muted:#666;--line:#e3e3e8;--card:#f6f6f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141417;--fg:#ececf1;--muted:#9a9aa5;--line:#2c2c33;--card:#1d1d22}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:24px 16px;max-width:1100px;margin:auto}}
h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}}
.k{{color:var(--muted);font-size:12px}} .v{{font-size:16px;font-variant-numeric:tabular-nums}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}}
</style></head><body>
<h1>TicketPilot telemetry</h1>
<div class="cards">{cards}</div>
{f'<h2>Before / after</h2><div class="scroll">{tbl(*cmp_table)}</div>' if cmp_table else ''}
<h2>Per step</h2><div class="scroll">{tbl(*step_table)}</div>
<h2>Most expensive tickets</h2><div class="scroll">{tbl(*ticket_table)}</div>
</body></html>"""
    Path(path).write_text(doc, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(ROOT / "out" / "telemetry"))
    ap.add_argument("--last", action="store_true", help="only the most recent run file")
    ap.add_argument("--compare", help="a 'before' summary .json (from --json) or telemetry file/dir to compare against")
    ap.add_argument("--html", help="also write an HTML dashboard to this path")
    ap.add_argument("--json", help="write the summary as JSON to this path")
    args = ap.parse_args()

    if not Path(args.path).exists():
        sys.exit(f"no telemetry at {args.path} - run `python run.py` first")
    records = load(args.path, args.last)
    summary = summarise(records)
    step_t, ticket_t = by_step(records), by_ticket(records)
    print(table(["metric", "value"], [[k, fmt(v)] for k, v in summary.items()]))
    print("\nPer step\n" + table(*step_t))
    print("\nMost expensive tickets\n" + table(*ticket_t))

    cmp_t = None
    if args.compare:
        before = json.loads(Path(args.compare).read_text()) if args.compare.endswith(".json") \
            else summarise(load(args.compare))
        cmp_t = compare(before, summary)
        print("\nBefore / after\n" + table(*cmp_t))
    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2))
    if args.html:
        write_html(args.html, summary, step_t, ticket_t, cmp_t)
        print(f"\nHTML dashboard: {args.html}")


if __name__ == "__main__":
    main()
