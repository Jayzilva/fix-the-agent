# Code Crunch: Fix the Agent

One-page version: [EVALUATION_CRITERIA.pdf](EVALUATION_CRITERIA.pdf)

TicketPilot works - it produces correct triage results - but it is expensive, slow and opaque.
Your job is to **Observe, Diagnose and Optimize** it without losing accuracy.

1. **Observe** - add telemetry. Right now the app records nothing: no traces, no usage, no cost.
   Build per-ticket and per-step visibility (tokens, cost, calls, turns, tool calls, latency).
2. **Diagnose** - use your telemetry to find what drives cost, tokens, calls and latency.
   Name each problem you find and show the evidence.
3. **Optimize** - fix the problems with clean, configurable engineering. Prove each fix with
   before/after numbers.

## How you are measured

Every API call goes through a judge proxy that records usage independently of your telemetry.
All metrics are per ticket over the judged ticket set.

| # | Criterion | Metric | Direction |
|---|---|---|---|
| C1 | Cost | USD per ticket (usage x model price table, plus Managed Agents session cost) | Lower |
| C2 | Input tokens | per ticket, split uncached / cache write / cache read | Lower uncached |
| C3 | Output tokens | per ticket, including thinking | Lower |
| C4 | Cache efficiency | cache_read / total input tokens (%) | Higher |
| C5 | Model mix | % of calls per tier (Opus / Sonnet / Haiku) | Cheapest tier that passes |
| C6 | LLM calls | model requests per ticket | Lower |
| C7 | Agent turns | turns per ticket; turn-cap hits | Lower, no cap hits |
| C8 | Tool behaviour | tool calls per ticket, tool error rate, duplicate calls | Lower |
| C9 | Latency | p50 and p95 seconds per ticket | Lower |
| C10 | Quality | accuracy on category, priority, KB ID, refund; reply pass rate | Must not drop |

**C10 is a gate:** if overall accuracy falls more than 2 percentage points below the baseline,
C1-C9 score zero.

## Scoring (100 points)

| Area | Points |
|---|---|
| Cost reduction (C1) - linear, full marks at >= 85% lower cost per ticket | 25 |
| Token and cache efficiency (C2-C4) | 10 |
| Calls, turns and tools (C6-C8) - zero turn-cap hits, tool error rate < 5% | 10 |
| Latency (C9) - p95 improvement | 5 |
| Model mix (C5) - each step on the cheapest tier that keeps C10 | 5 |
| Problems found - named and evidenced in your write-up | 10 |
| Observability built - working traces with per-ticket and per-step cost (live demo) | 15 |
| Diagnosis story - evidence (trace or chart) for each cost driver, before and after | 10 |
| Engineering quality - clean, configurable fixes; no hard-coded answers | 10 |

## Rules

- Do not change or bypass `ANTHROPIC_BASE_URL`.
- Do not hard-code answers or cache answers across runs on disk.
- Keep `app.pipeline.process_ticket(ticket)` as the entry point and keep the output fields.
- Any Claude surface is allowed. You may move work between the Agent SDK, Managed Agents, the
  Messages API and plain Python - choose what is cheapest while keeping quality.
- Clean up any cloud resources your runs create.

## Deliverables

- Your fixed repo.
- A write-up (`WRITEUP.md`): each problem found, the evidence, the fix, before/after numbers.
- A short live demo of your telemetry.
