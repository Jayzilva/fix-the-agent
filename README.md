# TicketPilot

TicketPilot triages customer support tickets for **Nimbus Cloud**, a (fictional) cloud hosting company.
For every ticket it produces one JSON result:

| Field | Values |
|---|---|
| `category` | `billing`, `technical`, `account`, `feature_request`, `other` |
| `priority` | `P1`, `P2`, `P3` |
| `kb_article_id` | knowledge base article ID (`KB-###`) or `null` |
| `reply_draft` | reply to the customer, max 120 words |
| `refund_eligible` | `true` / `false` |

It is built on three Claude surfaces:

- **Claude Agent SDK** (`claude-agent-sdk`) - optional agent backend (`app/orchestrator.py`)
- **Claude Messages API** (`anthropic`) - default triage call (`app/llm.py`)
- **Claude Managed Agents** - optional refund backend (`app/managed.py`)

See [docs/CHALLENGE.md](docs/CHALLENGE.md) for the Code Crunch challenge brief.

> **This is the reference solution** (branch `solution`). The default pipeline makes one cached
> Claude Haiku 5.5 call per ticket and does the refund check in Python. Measured on all 200 tickets:
> $0.0002 per ticket, p95 2.5 s, 99.5% accuracy. See [WRITEUP.md](WRITEUP.md) for every defect, its
> evidence and its fix.

## Setup

Python 3.10+ and the Claude Code CLI (used by the Agent SDK) are required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code   # if `claude --version` does not work yet
```

## Credentials

Set **one** of the following (see `.env.example`):

| Variable | Use |
|---|---|
| `ANTHROPIC_API_KEY` | Console API key. Works for all three surfaces. |
| `ANTHROPIC_AUTH_TOKEN` | Bearer token (e.g. from a gateway or `ant auth`). Messages API + Agent SDK. |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (`claude setup-token`). Agent SDK; Messages API with the OAuth beta header. |

Managed Agents needs `ANTHROPIC_API_KEY`. It is only used when `backends.refund: managed`. Claude Code
OAuth tokens work for the Messages API path because `app/config.py` adds the required identity block.

`ANTHROPIC_BASE_URL` is respected by every client. During judging it points at the event proxy - do not
change or override it in code.

## Run

```bash
python run.py                      # all 200 tickets -> out/results.jsonl
python run.py --limit 5            # first 5 tickets
python run.py --only T0002 T0017   # specific tickets
python run.py --concurrency 16     # tickets in flight
python -m unittest discover tests  # offline checks, no API calls
```

## Telemetry

Every call and step is logged to `out/telemetry/<run_id>.jsonl` (tokens, cache, cost, latency, ticket, step).

```bash
python scripts/telemetry_report.py --last                      # tables for the last run
python scripts/telemetry_report.py --html out/telemetry_report.html
python scripts/telemetry_report.py --last --json out/after.json
python scripts/telemetry_report.py --last --compare out/before.json
```

## Configuration

`config/settings.yaml` holds models, backends and pipeline settings.

```yaml
backends:
  triage: messages   # messages | sdk
  refund: python     # python | managed
```

Experiments override settings without editing them:
`TICKETPILOT_SETTINGS=config/experiments/sdk.yaml python run.py --limit 5`.

## Layout

```
app/
  pipeline.py       process_ticket(ticket) -> dict   (entry point used by the judge)
  llm.py            one structured-output triage call (default)
  refund.py         refund eligibility in Python
  telemetry.py      per-ticket/per-step usage, cost, latency; budgets
  orchestrator.py   optional Agent SDK backend (one lean agent per ticket)
  managed.py        optional Managed Agents refund backend
  tools/            typed MCP tools for the SDK backend
  prompts/          prompt templates
  kb.py, config.py
config/settings.yaml, config/prices.yaml, config/experiments/
scripts/telemetry_report.py
tests/
data/
  tickets.jsonl     200 tickets
  kb/               60 knowledge base articles
  customers.db      SQLite: plans, customers, charges
run.py
```

## Judging contract

The judge imports `app.pipeline.process_ticket` and calls it once per ticket (async or sync both work).
Keep that function name and signature, keep the output fields above, and keep reading data from `data/`.
