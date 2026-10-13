"""In-process MCP servers for the Agent SDK backend. Built once; each agent gets only what it needs."""
import functools

from claude_agent_sdk import create_sdk_mcp_server

from app.tools.crm_tools import CRM_TOOLS
from app.tools.kb_tools import KB_TOOLS


@functools.lru_cache(maxsize=None)
def mcp_server(name):
    tools = {"kb": KB_TOOLS, "crm": CRM_TOOLS}[name]
    return create_sdk_mcp_server(name=name, tools=tools)


def tool_names(name):
    tools = {"kb": KB_TOOLS, "crm": CRM_TOOLS}[name]
    return [f"mcp__{name}__{t.name}" for t in tools]
