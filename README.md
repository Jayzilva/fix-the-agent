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

- **Claude Agent SDK** (`claude-agent-sdk`) - specialist agents and a supervisor (`app/orchestrator.py`)
- **Claude Messages API** (`anthropic`) - reply writing/review and helpers (`app/llm.py`)
- **Claude Managed Agents** - refund check (`app/managed.py`)

See [docs/CHALLENGE.md](docs/CHALLENGE.md) for the Code Crunch challenge brief.

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

Managed Agents needs `ANTHROPIC_API_KEY`. With `backends.refund: auto` (default) the refund step runs on
Managed Agents when an API key is present and falls back to the Agent SDK refund agent otherwise.

`ANTHROPIC_BASE_URL` is respected by every client. During judging it points at the event proxy - do not
change or override it in code.

## Run

```bash
python run.py                      # all 200 tickets -> out/results.jsonl
python run.py --limit 5            # first 5 tickets
python run.py --only T0002 T0017   # specific tickets
```

## Configuration

`config/settings.yaml` holds models, backends and pipeline settings.

```yaml
backends:
  refund: auto    # managed | sdk | auto
```

The same work can be done on Managed Agents or with the Agent SDK. Managed Agents adds hosted
infrastructure (and its cost); pick what fits each step.

## Layout

```
app/
  pipeline.py       process_ticket(ticket) -> dict   (entry point used by the judge)
  orchestrator.py   Agent SDK specialist agents + supervisor
  llm.py            Messages API helpers, reply writer/reviewer
  managed.py        Managed Agents refund check
  tools/            MCP tools: knowledge base, CRM, utilities
  prompts/          prompt templates
  kb.py, config.py
config/settings.yaml
data/
  tickets.jsonl     200 tickets
  kb/               60 knowledge base articles
  customers.db      SQLite: plans, customers, charges
run.py
```

## Judging contract

The judge imports `app.pipeline.process_ticket` and calls it once per ticket (async or sync both work).
Keep that function name and signature, keep the output fields above, and keep reading data from `data/`.
