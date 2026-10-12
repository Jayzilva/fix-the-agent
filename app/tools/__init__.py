from claude_agent_sdk import create_sdk_mcp_server

from app.tools.crm_tools import CRM_TOOLS
from app.tools.kb_tools import KB_TOOLS
from app.tools.util_tools import UTIL_TOOLS


def build_mcp_servers():
    return {
        "kb": create_sdk_mcp_server(name="kb", tools=KB_TOOLS),
        "crm": create_sdk_mcp_server(name="crm", tools=CRM_TOOLS),
        "util": create_sdk_mcp_server(name="util", tools=UTIL_TOOLS),
    }


ALL_TOOL_NAMES = (
    [f"mcp__kb__{t.name}" for t in KB_TOOLS]
    + [f"mcp__crm__{t.name}" for t in CRM_TOOLS]
    + [f"mcp__util__{t.name}" for t in UTIL_TOOLS]
)
