import time

from claude_agent_sdk import tool

from app import telemetry
from app.kb import keyword_search


def _text(value, is_error=False):
    result = {"content": [{"type": "text", "text": value}]}
    if is_error:
        result["is_error"] = True
    return result


@tool(
    "search_kb",
    "Search the Nimbus Cloud knowledge base. Returns up to 3 matching articles as "
    "'KB-###: title' plus the issue each covers and its resolution. Use short keyword queries "
    "describing the customer's problem, e.g. 'build timeout deploy'.",
    {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Keywords describing the issue"}},
        "required": ["query"],
        "additionalProperties": False,
    },
)
async def search_kb(args):
    started = time.perf_counter()
    query = str(args.get("query") or "").strip()
    if not query:
        telemetry.record_tool_call("search_kb", False, time.perf_counter() - started)
        return _text("query must be a non-empty string", is_error=True)
    hits = keyword_search(query, limit=3)
    telemetry.record_tool_call("search_kb", True, time.perf_counter() - started)
    if not hits:
        return _text("No matching articles.")
    return _text("\n".join(
        f"{a['id']} [{a['category']}]: {a['title']}\n  Covers: {a['symptom'] or a['question']}\n  Resolution: {a['summary']}"
        for a in hits
    ))


KB_TOOLS = [search_kb]
