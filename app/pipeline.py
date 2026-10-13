"""TicketPilot pipeline: triage one ticket end to end.

  refund  - deterministic (app/refund.py) or Managed Agents, per backends.refund
  triage  - one structured-output call (app/llm.py) or one SDK agent, per backends.triage
  checks  - Python validation: KB ID exists, null KB for feature_request/other, reply word limit

Fresh context per ticket: nothing from earlier tickets is sent to the model.
"""
import asyncio
import logging

from app import llm, orchestrator, telemetry
from app.config import SETTINGS
from app.kb import article_ids, get_article
from app.refund import check_refund

log = logging.getLogger("ticketpilot")

FIELDS = ["category", "priority", "kb_article_id", "reply_draft", "refund_eligible"]
NO_ARTICLE = {"feature_request", "other"}


async def _refund(ticket):
    with telemetry.step("refund", backend=SETTINGS["backends"]["refund"]):
        decision = check_refund(ticket["customer_id"], ticket["created_at"])
        if not decision.found:
            log.warning("%s: customer %s not in CRM", ticket["ticket_id"], ticket["customer_id"])
        if SETTINGS["backends"]["refund"] == "managed":
            from app import managed

            eligible = await asyncio.to_thread(managed.check_refund, ticket)
            if eligible != decision.eligible:
                log.warning("%s: managed refund verdict %s differs from SQL %s",
                            ticket["ticket_id"], eligible, decision.eligible)
            decision = type(decision)(**{**decision.as_dict(), "eligible": eligible})
        return decision


def _normalise_kb(result):
    kb_id = result.get("kb_article_id")
    if result["category"] in NO_ARTICLE:
        return None
    if kb_id and str(kb_id).strip().upper() in article_ids():
        return str(kb_id).strip().upper()
    if kb_id:
        log.warning("model returned unknown KB id %r", kb_id)
    return None


def _trim(text, limit):
    words = text.split()
    if len(words) <= limit:
        return text
    cut = " ".join(words[:limit])
    end = cut.rfind(".")
    return cut[: end + 1] if end > len(cut) // 2 else cut


async def _check_reply(reply, limit):
    with telemetry.step("reply_check") as attrs:
        attrs["words"] = len(reply.split())
        for _ in range(SETTINGS["pipeline"]["reply_rewrite_attempts"]):
            if len(reply.split()) <= limit:
                break
            reply = await llm.shorten_reply(reply, limit)
        attrs["final_words"] = len(reply.split())
        return _trim(reply, limit)


async def process_ticket(ticket):
    with telemetry.ticket(ticket["ticket_id"]):
        refund = await _refund(ticket)

        backend = SETTINGS["backends"]["triage"]
        with telemetry.step("triage", backend=backend):
            triage = orchestrator.triage if backend == "sdk" else llm.triage
            result = await triage(ticket, refund)

        with telemetry.step("validate"):
            result["kb_article_id"] = _normalise_kb(result)
            article = get_article(result["kb_article_id"]) if result["kb_article_id"] else None
            if article and article["category"] != result["category"]:
                log.info("%s: category %s -> %s (from %s)", ticket["ticket_id"], result["category"],
                         article["category"], article["id"])
                result["category"] = article["category"]

        result["reply_draft"] = await _check_reply(result["reply_draft"].strip(),
                                                   SETTINGS["pipeline"]["reply_word_limit"])
        result["refund_eligible"] = refund.eligible
        return {"ticket_id": ticket["ticket_id"], **{f: result.get(f) for f in FIELDS}}
