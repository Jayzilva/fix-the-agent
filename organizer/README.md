# Organizer kit - TicketPilot / Code Crunch (organizers only)

On branch `main` (the participant starter) everything under `organizer/` is excluded via
`.git/info/exclude`, so participants see no hint of an answer key. This kit, the reference solution
and the evaluation skill live together on branch `solution`. `ANSWER_KEY.md` line numbers refer to
the starter code on `main`; run `build_answer_key.py` from a `main` checkout (on `solution` the
anchors are fixed, so it exits 1 by design). Participants only get the app, `data/` (tickets, KB,
customers.db) and `docs/CHALLENGE.md`, shipped as the participant zip built from `main`.

```
organizer/
  ANSWER_KEY.md          33 catalog defects + 5 bonus, with file:line (generated)
  defects.yaml           defect catalog with regex anchors (source for the key)
  build_answer_key.py    regenerates ANSWER_KEY.md; exits 1 if an anchor drifted
  judge/
    catalog.py           KB topics, feature requests, other tickets (dataset source)
    gen_data.py          generates data/ + judge/golden.jsonl (seeded, reproducible)
    golden.jsonl         labels
    proxy.py             logging/budget proxy (ANTHROPIC_BASE_URL target)
    worker.py            runs a slice of tickets through app.pipeline.process_ticket
    run_judged.py        N proxies + N workers, then score.py
    score.py             C1-C10 report + measured points vs a baseline
    prices.yaml          per-model prices (verify before the event)
    cleanup_managed.py   delete sessions/envs/files and archive agents left by runs
  eval/                  evaluation kit (used by the evaluate-submission skill)
    static_scan.py       per-defect PRESENT/PARTIAL/FIXED scan of a team repo (free)
    writeup_check.py     candidate defect IDs named in a team's WRITEUP.md (free)
    scorecard.py         100-point scorecard: measured 55 + judged 45, vs baseline and reference
    signals.yaml         bug signatures, fix signals and write-up keywords per defect
    reference-report.json  judged run of the reference solution (all 200 tickets)
  runs/<name>/           proxy logs, results, report.json, reply_judge.json, scorecard.md
.claude/skills/evaluate-submission/SKILL.md   Claude Code skill that runs the evaluation
```

## Reference solution

Branch `solution` (local worktree `../fix-the-agent-solution`) is the fixed app and the expected
write-up (`WRITEUP.md`). Judged run on all 200 tickets (2026-10-13): $0.0002/ticket, 1 LLM call,
97.7% cache reads, p95 2.5 s, accuracy 99.5% (category 100, priority 98, KB 100, refund 100, reply 99.5).

## Evaluating a team

In Claude Code at the repo root: "evaluate team-07 at ../team-07" (the `evaluate-submission` skill), or by hand:

```bash
python organizer/eval/static_scan.py   --repo ../team-07 --json organizer/runs/team-07/static_scan.json
python organizer/eval/writeup_check.py --repo ../team-07 --json organizer/runs/team-07/writeup.json
python organizer/judge/run_judged.py --name team-07 --repo ../team-07 --sample 40 --workers 4     --budget-usd 25 --baseline organizer/runs/baseline/report.json
python organizer/eval/scorecard.py --team team-07     # creates judged.yaml; fill it, re-run
```

`python organizer/eval/static_scan.py --calibrate` checks the scan against both branches (starter must
be 33/33 PRESENT, reference 0 PRESENT). Re-run it after editing `signals.yaml` or `defects.yaml`.

## Markers instead of `# CC-` comments

The spec asked for `# CC-<ID>` markers plus a strip step. Because the repo itself is what
participants clone, the committed code carries **no markers at all**. `defects.yaml` maps
each ID to regex anchors and `build_answer_key.py` resolves them to `file:line`. Re-run it
after any edit to the app; it fails if an anchor no longer matches.

## Before the event

1. Regenerate data if you change sizes:
   `python organizer/judge/gen_data.py --kb-words 700 --tickets 200`
   (spec said ~1,500 words/article; 700 halves baseline cost. Words in KB ~= tokens x 0.75.)
2. Smoke test on 2-3 tickets with a key that has a spend limit:
   `python organizer/judge/run_judged.py --name smoke --sample 3 --workers 1 --budget-usd 60 --verbose`
3. Full baseline dry run on the judged sample:
   `python organizer/judge/run_judged.py --name baseline --sample 40 --workers 4 --budget-usd 200`
   (`--budget-usd` is per worker/proxy.)
4. Check `runs/baseline/report.json`: overall C10 accuracy should be >= 90%. If not, tune the
   prompts in `app/prompts/` (then re-run `build_answer_key.py`).
5. Set team budgets at ~3x baseline cost and the per-ticket timeout / request cap from the
   observed baseline (defaults: 1800 s and 150 model requests; the spec's 5 min / 60 requests
   will cut the baseline short with this much waste - recalibrate after the dry run).
6. `python organizer/judge/cleanup_managed.py` (dry run) then `--apply`.

## Scoring a team

```bash
python organizer/judge/run_judged.py --name team-07 --repo ../team-07 --sample 40 --workers 4 \
    --budget-usd 600 --baseline organizer/runs/baseline/report.json
```

`report.json` has C1-C10 and `points` (the 55 measured points). The other 45 are judged
(defects named - compare against ANSWER_KEY.md, observability demo, diagnosis story,
engineering quality).

Judge-side notes:
- Each worker has its own proxy so requests are attributed to the ticket that worker is on,
  even if a team adds concurrency inside a ticket. Per-ticket latency (C9) is measured by the
  worker; teams' own cross-ticket concurrency in `run.py` is not part of the judged run.
- `sdk_turn` = /v1/messages requests from the Claude Code CLI (Agent SDK); `messages` = direct
  SDK calls. C7 turns counts `sdk_turn` requests.
- Managed Agents cost = `session.usage.list_cost` fetched after the run (needs an API key).
  `managed.sessions_left_open`, `agents_created_per_ticket`, `files_uploaded_per_ticket` and
  `session_api_requests_per_ticket` expose M1-M4.
- Reply pass/fail uses `claude-sonnet-5-5` directly (not through the proxy).
- Teams must keep `app.pipeline.process_ticket(ticket)`; async or sync both work.

## Baseline cost and time (estimate - confirm with the dry run)

Per pass of one ticket: ~14 Opus 5.5 Messages calls each carrying the ~65k-token KB system
prompt uncached (~$4), 5 Agent SDK subagent sessions with large tool results plus the supervisor
(~$1-3), one Managed Agents session with 61 file uploads. Two passes per ticket (L2).

- Roughly **$8-14 per ticket** and **15-25 min per ticket** sequentially.
- 40-ticket sample with 4 workers: ~$300-550, ~3 hours. Full 200: ~$1.6k-2.8k.
- A well-optimized submission lands around $0.01-0.05 per ticket and a few seconds.

Levers to make the baseline cheaper without removing any defect: `--kb-words 400`,
`max_review_rounds: 2`, a smaller `--sample`.

## Credentials

- `ANTHROPIC_API_KEY` covers all three surfaces (Managed Agents needs it).
- `ANTHROPIC_AUTH_TOKEN` / `CLAUDE_CODE_OAUTH_TOKEN` work for the Agent SDK; the Messages API path
  sends the `oauth-2025-04-20` beta header for `sk-ant-oat` tokens. Without an API key the refund
  step falls back to the SDK backend (`backends.refund: auto`). OAuth-only operation has not been
  exercised end to end - test it in the smoke run if teams will use it.

## Fixes made while building the reference solution

- `judge/proxy.py`: aiohttp's default DNS resolver failed on Windows ("Could not contact DNS servers").
  It now uses `ThreadedResolver`.
- `judge/score.py`: with a Claude Code OAuth token (`sk-ant-oat...`) the reply grader got 429. It now
  sends the Claude Code identity system block for OAuth tokens. `reply_judge.json` now stores
  `{pass, reason}` per ticket.
- The starter's Messages API path (`app/llm.py`) has the same OAuth limitation: with only an OAuth token,
  its Messages calls get 429. Teams on OAuth must add the identity block (see the reference
  `app/config.py:system_prefix`), or use an API key.

## Not done here

- The **baseline** (starter) has never been run live (~$8-14/ticket). The dry run in step 3 is still
  required: measured points need `runs/baseline/report.json`.
- The proxy, scorer and reply grader have been run live against the reference solution (all 200 tickets).
- The reference `backends.refund: managed` path was not run live (no API key was available); the Agent
  SDK backend was smoke-tested.
