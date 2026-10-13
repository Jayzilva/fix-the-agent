---
name: evaluate-submission
description: Score a Code Crunch "Fix the Agent" (TicketPilot) team submission out of 100. Runs the free static defect scan and write-up check, optionally the paid judged run, reviews the team's telemetry and fixes against the broken starter and the reference solution, and writes organizer/runs/<team>/scorecard.md. Use when an organizer or judge says "evaluate team X", "score this submission", "judge this repo", or asks how a TicketPilot fix compares with the reference.
---

# Evaluate a TicketPilot submission

You are helping a hackathon judge score one team's fixed TicketPilot repo. The rubric is in
`docs/CHALLENGE.md`: 55 points are measured by the judge harness and 45 are judged. This skill
gathers the evidence and drafts the judged parts. The human judge makes the final call.

**Organizer-only.** The skill reads `organizer/defects.yaml`, `organizer/ANSWER_KEY.md` and the
reference solution. Never copy them into a team repo or show them to participants.

## Reference points

| | Where | What it is |
|---|---|---|
| Broken starter | git branch `main` (and the participant zip) | 33 planted defects (A1-A10, B1-B6, M1-M5, T1-T5, L1-L3, O1-O4) + 5 bonus (X1-X5) |
| Reference solution | git branch `solution` (worktree `../fix-the-agent-solution`) | all defects fixed; `WRITEUP.md` shows the expected write-up |
| Reference metrics | `organizer/eval/reference-report.json` | all 200 tickets: $0.0002/ticket, 1 call, 97.7% cache read, p95 2.5 s, 99.5% accuracy |
| Baseline metrics | `organizer/runs/baseline/report.json` | starter app dry run; required for measured points |

A strong team lands near the reference metrics. Full C1 marks need >= 85% cost reduction against the baseline.

## Workflow

Ask only for what is missing: the **team name** (used as the run name) and the **path to their repo**.
Run every command from the organizer repo root.

### 1. Static defect scan (free)

```bash
python organizer/eval/static_scan.py --repo <team_repo> --json organizer/runs/<team>/static_scan.json
```

- `PRESENT` / `PARTIAL`: the starter's bug signature is still in the code. Open the cited `file:line` and confirm.
- `FIXED`: no signature left and a fix signal was found.
- `LIKELY_FIXED`: the code was removed or rewritten. Skim it.
- `UNKNOWN`: the signature is gone and no fix signal was found. Check by hand (for example, the team may have dropped the SDK entirely, so `max_turns` is not needed).

The scan is evidence, not a verdict. A renamed function can hide a defect that is still there. If
`signals.yaml` or `defects.yaml` changes, run `python organizer/eval/static_scan.py --calibrate`.
It must report the starter as 33 PRESENT and the reference as 0 PRESENT.

### 2. Write-up check (free)

```bash
python organizer/eval/writeup_check.py --repo <team_repo> --json organizer/runs/<team>/writeup.json
```

This lists candidate defect IDs matched by keywords. For each candidate, read the snippet and the
surrounding write-up. Confirm it only if the team **names the problem and gives evidence** (a trace,
chart or before/after numbers). Also scan the write-up for real problems the matcher missed: compare
against `organizer/ANSWER_KEY.md`. Bonus findings X1-X5 do not count toward the 10 points, but note them
for Engineering quality. Points = confirmed IDs // 3, capped at 10.

### 3. Measured run (costs money - confirm with the user first)

Tell the user the expected cost before running. A well-fixed repo costs cents for 40 tickets, but a
barely-fixed one can cost hundreds of dollars. Always pass a budget.

```bash
python organizer/judge/run_judged.py --name <team> --repo <team_repo> --sample 40 --workers 4 \
    --budget-usd 25 --baseline organizer/runs/baseline/report.json
```

If `report.json` already exists, do not re-run. If there is no baseline report yet, the run still
produces metrics but no `points`. Say so, and leave the measured points for after the baseline dry run.

Check the run before trusting it:
- `errors` in `report.json`: tickets that crashed count against accuracy.
- `C10_accuracy_pct.overall` against the baseline: the **quality gate** fails if it is more than 2 pp lower. Then C1-C9 score 0.
- `managed.sessions_left_open` > 0, or `agents_created_per_ticket` > 0: M1/M2 regressions.
- `budget_rejections` or `C7_cap_hits`: the run was cut short.
- Hard-coded answers: if accuracy is suspiciously perfect with ~0 output tokens, grep the repo for golden labels, ticket-ID lookup tables, or answer files under `out/` or `data/` read across runs (forbidden).

### 4. Judged areas (draft scores with evidence)

Read the team's code and write-up. Draft a score and a one-line reason for each. Ask the judge to
adjust after the live demo.

**Observability (15)**: is there a working trace with cost **per ticket and per step**?
- 13-15: per-call records with uncached / cache-write / cache-read / output tokens, USD, latency, ticket + step tags; an aggregated view (dashboard, report or tracing UI); live demo works. Optional: budgets or alerts.
- 8-12: per-ticket cost and tokens, but per-step attribution is weak or Agent SDK / Managed costs are missing.
- 3-7: logs `response.usage` somewhere with no aggregation or tagging.
- 0-2: nothing beyond print statements.
The reference implements this in `app/telemetry.py` + `scripts/telemetry_report.py`.

**Diagnosis story (10)**: is there evidence (trace or chart) for each cost driver, before and after?
- Full marks: each major driver (model tier, uncached KB prompt, broken cache prefix, output and thinking bloat, call fan-out, re-run loops, managed session overhead) has before/after numbers from their own telemetry.
- Deduct where numbers are missing, estimated rather than measured, or contradicted by `report.json`.

**Engineering quality (10)**: clean, configurable fixes.
- Settings-driven (models, effort, backends, budgets) instead of hard-coded constants.
- No hard-coded answers, no cross-run answer cache, `ANTHROPIC_BASE_URL` untouched, `process_ticket` and its output fields intact.
- Static scan has no PRESENT / PARTIAL left, or the ones left are justified.
- Errors handled specifically (no bare `except: pass`), retries only on retryable errors, cloud resources cleaned up.
- Bonus findings X1-X5 found and fixed: credit here.

Record the judged scores in `organizer/runs/<team>/judged.yaml`. The first scorecard run creates it,
pre-filled with the write-up candidates.

### 5. Scorecard

```bash
python organizer/eval/scorecard.py --team <team>
```

This writes `organizer/runs/<team>/scorecard.md` and `scorecard.json`: points table, metrics for
baseline vs team vs reference, the static scan, and the write-up candidates. Re-run it after every edit
to `judged.yaml`.

## Reporting back

Give the judge a short summary:
- the total, and which parts are still pending (no baseline, or judged fields empty)
- the 3 biggest wins and the 3 biggest misses compared with the reference (cite metrics and `file:line`)
- anything suspicious (gate failure, hard-coding, resources left open)
- the path to `scorecard.md`

Do not inflate scores to be kind, and do not deduct for choices the rules allow. Any Claude surface
is allowed, as long as quality holds.
