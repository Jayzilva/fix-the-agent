import json
import time

from claude_agent_sdk import tool

from app import telemetry
from app.refund import check_refund as decide_refund


def _text(value, is_error=False):
    result = {"content": [{"type": "text", "text": value}]}
    if is_error:
        result["is_error"] = True
    return result


@tool(
    "check_refund",
    "Decide refund eligibility for one customer as of the ticket date. Returns plan, last successful "
    "charge, days since that charge, the plan's refund window and the eligible flag.",
    {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "pattern": r"^C\d{4}$"},
            "as_of": {"type": "string", "format": "date", "description": "Ticket date, YYYY-MM-DD"},
        },
        "required": ["customer_id", "as_of"],
        "additionalProperties": False,
    },
)
async def check_refund(args):
    started = time.perf_counter()
    try:
        decision = decide_refund(args["customer_id"], args["as_of"])
    except (KeyError, ValueError) as e:
        telemetry.record_tool_call("check_refund", False, time.perf_counter() - started)
        return _text(f"invalid input: {e}", is_error=True)
    telemetry.record_tool_call("check_refund", decision.found, time.perf_counter() - started)
    if not decision.found:
        return _text(f"customer {args['customer_id']} not found", is_error=True)
    return _text(json.dumps(decision.as_dict()))


CRM_TOOLS = [check_refund]
