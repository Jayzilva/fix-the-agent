"""Build a team's 100-point scorecard (organizer only, no API calls).

Inputs, all in organizer/runs/<team>/:
  report.json         from run_judged.py --baseline ... (measured 55 points: C1-C9 + quality gate)
  static_scan.json    from static_scan.py --json
  writeup.json        from writeup_check.py --json
  judged.yaml         judge's manual scores; created as a template on the first run

  python organizer/eval/scorecard.py --team team-07
  python organizer/eval/scorecard.py --team team-07 --reference organizer/eval/reference-report.json

Writes organizer/runs/<team>/scorecard.md and scorecard.json.
"""
import argparse
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"

JUDGED_MAX = {"observability": 15, "diagnosis": 10, "engineering": 10}
MEASURED = [("C1", "Cost reduction", 25), ("C2_C4", "Token & cache efficiency", 10),
            ("C6_C8", "Calls, turns, tools", 10), ("C9", "Latency p95", 5), ("C5", "Model mix", 5)]
METRICS = [
    ("Cost / ticket (USD)", lambda r: r["C1_cost_usd_per_ticket"]),
    ("Uncached input / ticket", lambda r: r["C2_input_tokens_per_ticket"]["uncached"]),
    ("Cache read / ticket", lambda r: r["C2_input_tokens_per_ticket"]["cache_read"]),
    ("Output tokens / ticket", lambda r: r["C3_output_tokens_per_ticket"]),
    ("Cache read %", lambda r: r["C4_cache_read_pct"]),
    ("Model mix %", lambda r: r["C5_model_mix_pct"]),
    ("LLM calls / ticket", lambda r: r["C6_llm_calls_per_ticket"]),
    ("Agent turns / ticket", lambda r: r["C7_agent_turns_per_ticket"]),
    ("Turn-cap hits", lambda r: r["C7_cap_hits"]),
    ("Tool calls / ticket", lambda r: r["C8_tool_calls_per_ticket"]),
    ("Tool error %", lambda r: r["C8_tool_error_rate_pct"]),
    ("Latency p50 / p95 (s)", lambda r: f"{r['C9_latency_s']['p50']} / {r['C9_latency_s']['p95']}"),
    ("Accuracy overall %", lambda r: r["C10_accuracy_pct"]["overall"]),
    ("Reply pass %", lambda r: r["C10_accuracy_pct"].get("reply_pass")),
    ("Managed sessions left open", lambda r: r["managed"]["sessions_left_open"]),
    ("Ticket errors", lambda r: len(r.get("errors") or {})),
]

JUDGED_TEMPLATE = """# Judge scores for {team}. Fill in, then re-run scorecard.py.
# defects_confirmed: catalog IDs the write-up names AND evidences (trace, chart or numbers).
#   Candidates from writeup_check.py are pre-filled; delete the ones that are not evidenced,
#   add any it missed. Points = len(confirmed) // 3, cap 10.
defects_confirmed: {candidates}

# 0-15: working traces with per-ticket AND per-step cost, shown live. Full marks need tokens
#       (uncached/cache/out), cost, calls, latency per step and per ticket, plus a demo.
observability: null
# 0-10: evidence (trace or chart) for each cost driver, before and after.
diagnosis: null
# 0-10: clean, configurable fixes; no hard-coded answers; no cross-run answer caching on disk.
engineering: null

notes: |

"""


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def safe(fn, report):
    if not report:
        return "-"
    try:
        return fn(report)
    except (KeyError, TypeError):
        return "-"


def build(team, reference_path):
    run = RUNS / team
    report = load_json(run / "report.json")
    static = load_json(run / "static_scan.json")
    writeup = load_json(run / "writeup.json")
    baseline_path = RUNS / "baseline" / "report.json"
    baseline = load_json(baseline_path)
    reference = load_json(Path(reference_path)) if reference_path else None

    judged_path = run / "judged.yaml"
    if not judged_path.exists():
        candidates = sorted((writeup or {}).get("found", {}))
        judged_path.parent.mkdir(parents=True, exist_ok=True)
        judged_path.write_text(JUDGED_TEMPLATE.format(team=team, candidates=json.dumps(candidates)), encoding="utf-8")
    judged = yaml.safe_load(judged_path.read_text(encoding="utf-8")) or {}

    points = (report or {}).get("points") or {}
    gate = points.get("quality_gate")
    measured = {key: (points.get(key, 0.0) if gate else 0.0) for key, _, _ in MEASURED}
    confirmed = judged.get("defects_confirmed") or []
    defects_pts = min(10, len(confirmed) // 3)
    manual = {k: judged.get(k) for k in JUDGED_MAX}
    total = sum(measured.values()) + defects_pts + sum(v or 0 for v in manual.values())
    pending = [k for k, v in manual.items() if v is None]

    lines = [f"# Scorecard - {team}", ""]
    if not report:
        lines += ["> No `report.json` yet: run `run_judged.py` for this team. Measured points count as 0.", ""]
    elif not points:
        lines += ["> `report.json` has no `points`: re-score with `--baseline organizer/runs/baseline/report.json`.", ""]
    elif not gate:
        lines += ["> **Quality gate failed** (accuracy more than 2 pp below baseline): C1-C9 score 0.", ""]
    if pending:
        lines += [f"> Judged scores still empty in `judged.yaml`: {', '.join(pending)}.", ""]

    lines += ["## Points", "", "| Area | Points | Max |", "|---|---|---|"]
    lines += [f"| {label} | {measured[key]:.2f} | {mx} |" for key, label, mx in MEASURED]
    lines += [f"| Problems found ({len(confirmed)} confirmed IDs) | {defects_pts} | 10 |"]
    lines += [f"| {k.capitalize()} | {'-' if v is None else v} | {JUDGED_MAX[k]} |" for k, v in manual.items()]
    lines += [f"| **Total** | **{total:.2f}** | **100** |", ""]

    lines += ["## Metrics: baseline vs team vs reference", "",
              "| Metric | Baseline | Team | Reference |", "|---|---|---|---|"]
    lines += [f"| {name} | {safe(fn, baseline)} | {safe(fn, report)} | {safe(fn, reference)} |" for name, fn in METRICS]
    lines += [""]

    if static:
        lines += ["## Static defect scan", "", "Counts: " + ", ".join(f"{k} {v}" for k, v in static["counts"].items()), "",
                  "| ID | Status | Defect | Evidence |", "|---|---|---|---|"]
        for d in static["defects"]:
            evidence = ", ".join(d["anchors_still_matching"] or d["fix_signals"])[:100]
            lines.append(f"| {d['id']} | {d['status']} | {d['title'][:70]} | {evidence} |")
        lines += ["", "PRESENT / PARTIAL rows still carry the starter's bug signature; check them before scoring "
                      "Engineering quality. LIKELY_FIXED means the code was removed or rewritten.", ""]

    if writeup:
        lines += ["## Write-up candidates", "", f"File: `{writeup['file']}` - {writeup['candidates']} candidate IDs "
                  f"(confirmed: {', '.join(confirmed) or 'none yet'})", ""]
        for defect_id, info in (writeup.get("found") or {}).items():
            mark = "x" if defect_id in confirmed else " "
            lines.append(f"- [{mark}] **{defect_id}** {'(numbers)' if info['has_numbers'] else '(no numbers)'}: "
                         f"{info['snippet'][:160]}")
        lines.append("")

    if judged.get("notes"):
        lines += ["## Judge notes", "", str(judged["notes"]).strip(), ""]

    out = {"team": team, "total": round(total, 2), "measured": measured, "quality_gate": gate,
           "defects_confirmed": confirmed, "defects_points": defects_pts, "judged": manual, "pending": pending}
    (run / "scorecard.md").write_text("\n".join(lines), encoding="utf-8")
    (run / "scorecard.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {run / 'scorecard.md'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", required=True, help="run name under organizer/runs/")
    ap.add_argument("--reference", default=str(HERE / "reference-report.json"))
    args = ap.parse_args()
    build(args.team, args.reference)
