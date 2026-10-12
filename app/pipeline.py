"""TicketPilot pipeline: triage one ticket end to end."""
import asyncio
import functools
import json

from app import llm, managed, orchestrator
from app.config import SETTINGS, refund_backend

FIELDS = ["category", "priority", "kb_article_id", "reply_draft", "refund_eligible"]


def retry(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        error = None
        for _ in range(5):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                error = e
        raise error

    return wrapper


def merge_answers(ticket, answers):
    specialist_notes = "\n\n".join(
        f"### {field} specialist\n{orchestrator.final_answer(text)}" for field, text in answers.items()
    )
    return llm.ask_json(
        "Combine the specialist answers below into one JSON object with exactly these keys: "
        f"{', '.join(FIELDS)}. Use JSON null for a missing article and true/false for refund_eligible.\n\n"
        f"Ticket:\n{json.dumps(ticket, indent=2)}\n\n{specialist_notes}"
    )


async def triage_once(ticket):
    answers = await orchestrator.run_field_agents(ticket)
    result = merge_answers(ticket, answers)

    try:
        result["kb_article_id"] = llm.lookup_article_id(result.get("kb_article_id"))
    except:
        pass

    result["reply_draft"] = llm.review_loop(ticket, result, draft=result.get("reply_draft"))

    if refund_backend() == "managed":
        try:
            result["refund_eligible"] = await asyncio.to_thread(managed.check_refund, ticket)
        except:
            pass
    result["refund_eligible"] = str(result.get("refund_eligible")).lower() == "true"
    return result


@retry
async def process_ticket(ticket):
    result = None
    for _ in range(SETTINGS["pipeline"]["max_passes"]):
        result = await triage_once(ticket)
        confidence = await orchestrator.supervisor_confidence(ticket, result)
        if confidence >= SETTINGS["pipeline"]["confidence_threshold"]:
            break
    output = {"ticket_id": ticket["ticket_id"], **{f: result.get(f) for f in FIELDS}}
    llm.remember(ticket, output)
    return output
