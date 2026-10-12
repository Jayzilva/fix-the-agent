import asyncio
import json
from datetime import datetime

from claude_agent_sdk import tool

from app import llm


def _text(value):
    return {"content": [{"type": "text", "text": value}]}


@tool("count_words", "Counts words.", {"type": "object", "properties": {"text": {}}})
async def count_words(args):
    return _text(str(await asyncio.to_thread(llm.count_words, args.get("text", ""))))


@tool("days_since", "Days since a date.", {"type": "object", "properties": {"date": {}, "as_of": {}}})
async def days_since(args):
    as_of = args.get("as_of") or datetime.now().date().isoformat()
    return _text(str(await asyncio.to_thread(llm.days_between, args.get("date"), as_of)))


@tool("format_json", "Formats JSON.", {"type": "object", "properties": {"text": {}}})
async def format_json(args):
    data = await asyncio.to_thread(
        llm.ask_json, f"Convert this into a valid JSON object:\n\n{args.get('text', '')}"
    )
    return _text(json.dumps(data))


@tool("current_time", "Current time.", {"type": "object", "properties": {}})
async def current_time(args):
    return _text(datetime.now().isoformat())


UTIL_TOOLS = [count_words, days_since, format_json, current_time]
