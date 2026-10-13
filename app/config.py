import os
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "app" / "prompts"

def _merge(base, override):
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


with open(ROOT / "config" / "settings.yaml", encoding="utf-8") as f:
    SETTINGS = yaml.safe_load(f)

# Optional experiment overrides, e.g. TICKETPILOT_SETTINGS=config/experiments/sdk.yaml
if os.environ.get("TICKETPILOT_SETTINGS"):
    with open(ROOT / os.environ["TICKETPILOT_SETTINGS"], encoding="utf-8") as f:
        _merge(SETTINGS, yaml.safe_load(f))

KB_DIR = ROOT / SETTINGS["paths"]["kb"]
DB_PATH = ROOT / SETTINGS["paths"]["customers_db"]
TICKETS_PATH = ROOT / SETTINGS["paths"]["tickets"]
OUTPUT_PATH = ROOT / SETTINGS["paths"]["output"]


def load_prompt(name):
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _credentials():
    """Client kwargs from whatever credentials are in the environment.

    Supports ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN and CLAUDE_CODE_OAUTH_TOKEN.
    ANTHROPIC_BASE_URL is picked up by the SDK automatically - never override it.
    """
    llm = SETTINGS["llm"]
    kwargs = {"max_retries": llm["max_retries"], "timeout": llm["timeout_s"]}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return {**kwargs, "api_key": api_key}
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token:
        headers = {"anthropic-beta": "oauth-2025-04-20"} if token.startswith("sk-ant-oat") else None
        return {**kwargs, "auth_token": token, "default_headers": headers}
    return kwargs


_sync_client = None
_async_client = None


def make_client():
    """One shared sync client per process (connection reuse, one place for retries)."""
    global _sync_client
    if _sync_client is None:
        _sync_client = anthropic.Anthropic(**_credentials())
    return _sync_client


def make_async_client():
    """One shared async client per process."""
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(**_credentials())
    return _async_client


def uses_claude_code_oauth():
    return not os.environ.get("ANTHROPIC_API_KEY") and (
        os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or ""
    ).startswith("sk-ant-oat")


def system_prefix():
    """Claude Code OAuth tokens are only accepted on the Messages API (else 429) when the system
    prompt opens with the Claude Code identity block. Static, so it stays inside the cached prefix."""
    if uses_claude_code_oauth():
        return [{"type": "text", "text": "You are Claude Code, Anthropic's official CLI for Claude."}]
    return []


def has_api_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
