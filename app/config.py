import os
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "app" / "prompts"

with open(ROOT / "config" / "settings.yaml", encoding="utf-8") as f:
    SETTINGS = yaml.safe_load(f)

KB_DIR = ROOT / SETTINGS["paths"]["kb"]
DB_PATH = ROOT / SETTINGS["paths"]["customers_db"]
TICKETS_PATH = ROOT / SETTINGS["paths"]["tickets"]
OUTPUT_PATH = ROOT / SETTINGS["paths"]["output"]


def load_prompt(name):
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def make_client():
    """Build an Anthropic client from whatever credentials are in the environment.

    Supports ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN and CLAUDE_CODE_OAUTH_TOKEN.
    ANTHROPIC_BASE_URL is picked up by the SDK automatically.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token:
        headers = {"anthropic-beta": "oauth-2025-04-20"} if token.startswith("sk-ant-oat") else None
        return anthropic.Anthropic(auth_token=token, default_headers=headers)
    return anthropic.Anthropic()


def has_api_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def refund_backend():
    backend = SETTINGS["backends"]["refund"]
    if backend == "auto":
        return "managed" if has_api_key() else "sdk"
    return backend
