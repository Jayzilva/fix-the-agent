"""Claude Agent SDK backend (backends.triage = sdk): one lean agent per ticket.

The default pipeline uses one Messages API call instead (app/llm.py), which is cheaper.
This backend is kept for teams that want an agent: it gets a single KB search tool,
a hard turn cap, an SDK-enforced USD budget and structured output.
"""
import json
import time

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from app import telemetry
from app.config import ROOT, SETTINGS, load_prompt
from app.llm import TRIAGE_SCHEMA, ticket_message
from app.tools import mcp_server, tool_names

SDK = SETTINGS["sdk"]


def agent_options():
    return ClaudeAgentOptions(
        model=SETTINGS["models"]["sdk_agent"],
        system_prompt=load_prompt("agent_system.md"),
        mcp_servers={"kb": mcp_server("kb")},
        allowed_tools=tool_names("kb"),
        tools=[],                    # no built-in Claude Code tools
        permission_mode="bypassPermissions",
        max_turns=SDK["max_turns"],
        max_budget_usd=SDK["max_budget_usd"],
        effort=SDK["effort"],
        output_format={"type": "json_schema", "schema": TRIAGE_SCHEMA},
        setting_sources=[],
        cwd=str(ROOT),
    )


async def triage(ticket, refund):
    """Fresh session per ticket (no shared supervisor, no history)."""
    telemetry.check_budget()
    started = time.perf_counter()
    result = None
    tool_calls = 0
    async for message in query(prompt=ticket_message(ticket, refund), options=agent_options()):
        if isinstance(message, ResultMessage):
            result = message
        elif getattr(message, "content", None):
            tool_calls += sum(1 for b in message.content if type(b).__name__ == "ToolUseBlock")
    if result is None:
        raise RuntimeError("agent produced no result")
    telemetry.record_agent_run(
        "agent_sdk", SETTINGS["models"]["sdk_agent"], cost_usd=result.total_cost_usd, usage=result.usage,
        turns=result.num_turns, tool_calls=tool_calls, latency_s=time.perf_counter() - started,
        extra={"session_id": result.session_id, "subtype": result.subtype},
    )
    if result.is_error:
        raise RuntimeError(f"agent run failed: {result.subtype} {result.errors}")
    if result.structured_output:
        return result.structured_output
    return json.loads(result.result)


async def close():
    """Nothing long-lived to close; kept so run.py does not care which backend ran."""
