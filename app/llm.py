"""Triage on the Claude Messages API: one structured-output call per ticket.

The system prompt (rules + compact KB index) is static and cached; everything that changes per
ticket goes in the user turn, after the cache breakpoint.
"""
import functools
import json
import logging
import time

from app import telemetry
from app.config import SETTINGS, load_prompt, make_async_client, system_prefix
from app.kb import kb_index

log = logging.getLogger("ticketpilot")

LLM = SETTINGS["llm"]
CATEGORIES = ["billing", "technical", "account", "feature_request", "other"]

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "priority": {"type": "string", "enum": ["P1", "P2", "P3"]},
        "kb_article_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "reply_draft": {"type": "string"},
    },
    "required": ["category", "priority", "kb_article_id", "reply_draft"],
    "additionalProperties": False,
}


@functools.lru_cache(maxsize=1)
def system_blocks():
    cache_control = {"type": "ephemeral"}
    if LLM["cache_ttl"] == "1h":
        cache_control["ttl"] = "1h"
    return system_prefix() + [{"type": "text", "text": load_prompt("triage_system.md") + "\n" + kb_index(),
                               "cache_control": cache_control}]


def _thinking():
    return {"type": "disabled"} if LLM["thinking"] == "disabled" else {"type": "adaptive"}


async def create(model, messages, *, max_tokens=None, schema=None, system=None):
    """One Messages API call with budget check and telemetry. Retries are the SDK's (429/5xx only)."""
    telemetry.check_budget()
    output_config = {"effort": LLM["effort"]}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    started = time.perf_counter()
    response = await make_async_client().messages.create(
        model=model,
        max_tokens=max_tokens or LLM["max_tokens"],
        system=system_blocks() if system is None else system_prefix() + system,
        thinking=_thinking(),
        output_config=output_config,
        messages=messages,
    )
    telemetry.record_llm_call("messages", model, response.usage, time.perf_counter() - started,
                              request_id=getattr(response, "_request_id", None), stop_reason=response.stop_reason)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"response truncated at max_tokens={max_tokens or LLM['max_tokens']}")
    return "".join(b.text for b in response.content if b.type == "text")


def ticket_message(ticket, refund):
    facts = {"refund_eligible": refund.eligible}
    return (
        f"<ticket>\n{json.dumps({k: ticket[k] for k in ('subject', 'body', 'created_at')}, indent=1)}\n</ticket>\n"
        f"<billing_system>\n{json.dumps(facts)}\n</billing_system>"
    )


async def triage(ticket, refund):
    model = SETTINGS["models"]["triage"]
    messages = [{"role": "user", "content": ticket_message(ticket, refund)}]
    text = await create(model, messages, schema=TRIAGE_SCHEMA)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:  # structured outputs should make this unreachable
        raise RuntimeError(f"triage returned invalid JSON: {text[:200]!r}") from e


async def shorten_reply(reply, limit):
    """Targeted rewrite when the reply is over the word limit (rare with the prompt's 100-word target)."""
    messages = [{"role": "user", "content": (
        f"Rewrite this customer support reply in at most {limit - 20} words. Keep the concrete next step "
        f"and the sign-off. Return only the reply.\n\n<reply>\n{reply}\n</reply>")}]
    return (await create(SETTINGS["models"]["triage"], messages, max_tokens=400)).strip()
