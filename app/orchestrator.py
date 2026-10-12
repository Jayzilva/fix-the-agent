"""Claude Agent SDK orchestration: one specialist subagent per output field plus a supervisor."""
import json
import re

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, query

from app import llm
from app.config import ROOT, SETTINGS, load_prompt
from app.tools import ALL_TOOL_NAMES, build_mcp_servers

FIELD_INSTRUCTIONS = {
    "category": "Decide the ticket category: billing, technical, account, feature_request or other.",
    "priority": "Decide the ticket priority: P1, P2 or P3, following the priority rules exactly.",
    "kb_article_id": "Find the single most relevant knowledge base article and give its ID (KB-###), "
                     "or null for feature_request and other tickets.",
    "reply_draft": "Draft the reply to the customer (at most 120 words).",
    "refund_eligible": "Decide whether the customer is eligible for a refund under the refund policy "
                       "as of the ticket date. Answer true or false.",
}

_supervisor = None


def agent_options(model):
    return ClaudeAgentOptions(
        model=model,
        system_prompt=load_prompt("agent_system.md"),
        mcp_servers=build_mcp_servers(),
        allowed_tools=ALL_TOOL_NAMES,
        tools=[],
        permission_mode="bypassPermissions",
        effort="high",
        setting_sources=[],
        cwd=str(ROOT),
        env={"MAX_MCP_OUTPUT_TOKENS": "150000"},
    )


def parent_context(ticket):
    lines = ["# Full context", "", "## Current ticket", json.dumps(ticket, indent=2), ""]
    if llm.HISTORY:
        lines += ["## Tickets already handled in this session"]
        lines += [m["content"] for m in llm.HISTORY]
    return "\n".join(lines)


async def run_subagent(field, ticket):
    prompt = parent_context(ticket) + "\n\n" + load_prompt("subagent_task.md").format(
        field=field, instructions=FIELD_INSTRUCTIONS[field]
    )
    result_text = ""
    async for message in query(prompt=prompt, options=agent_options(SETTINGS["models"]["subagents"])):
        if isinstance(message, ResultMessage):
            result_text = message.result or ""
    return result_text


async def run_field_agents(ticket):
    answers = {}
    for field in FIELD_INSTRUCTIONS:
        answers[field] = await run_subagent(field, ticket)
    return answers


def final_answer(text):
    match = re.findall(r"FINAL ANSWER:\s*(.+)", text or "", re.S)
    return match[-1].strip() if match else (text or "").strip()


async def supervisor_confidence(ticket, result):
    global _supervisor
    if _supervisor is None:
        _supervisor = ClaudeSDKClient(options=agent_options(SETTINGS["models"]["orchestrator"]))
        await _supervisor.connect()
    await _supervisor.query(
        load_prompt("supervisor.md").format(ticket=json.dumps(ticket, indent=2), result=json.dumps(result, indent=2))
    )
    text = ""
    async for message in _supervisor.receive_response():
        if isinstance(message, ResultMessage):
            text = message.result or ""
    found = re.findall(r"CONFIDENCE:\s*([0-9.]+)", text)
    return float(found[-1]) if found else 0.0


async def close():
    global _supervisor
    if _supervisor is not None:
        await _supervisor.disconnect()
        _supervisor = None
