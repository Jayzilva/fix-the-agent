"""Refund check on Claude Managed Agents (backends.refund = managed).

Off by default: refund eligibility is one SQL query + date math (app/refund.py), so a hosted
session only adds cost and latency. When enabled, the expensive parts happen once per process:

- agent + environment: created once (or reused from TICKETPILOT_REFUND_AGENT_ID /
  TICKETPILOT_REFUND_ENV_ID), never per ticket
- only customers.db is uploaded, once; the KB is not mounted (the check does not need it)
- the session is streamed (no polling), capped by a session budget, and deleted afterwards

`python -m app.managed --cleanup` deletes everything this process type created.
"""
import argparse
import atexit
import logging
import os
import re
import threading
import time

from app import telemetry
from app.config import DB_PATH, SETTINGS, load_prompt, make_client

log = logging.getLogger("ticketpilot")
CFG = SETTINGS["managed"]
NAME_PREFIX = "ticketpilot-refund"

AGENT_TOOLS = [{
    "type": "agent_toolset_20260401",
    "default_config": {"enabled": True, "permission_policy": {"type": "always_allow"}},
    "configs": [{"name": "web_fetch", "enabled": False}, {"name": "web_search", "enabled": False}],
}]

_lock = threading.Lock()
_resources = {}


def _ensure_resources(client):
    with _lock:
        if _resources:
            return _resources
        env_id = os.environ.get("TICKETPILOT_REFUND_ENV_ID")
        if not env_id:
            env_id = client.beta.environments.create(
                name=f"{NAME_PREFIX}-env", config={"type": "cloud", "networking": {"type": "limited"}},
            ).id
        agent_id = os.environ.get("TICKETPILOT_REFUND_AGENT_ID")
        if agent_id:
            agent = client.beta.agents.retrieve(agent_id)
        else:
            agent = client.beta.agents.create(
                name=NAME_PREFIX, model=SETTINGS["models"]["refund_agent"],
                system=load_prompt("refund_agent.md"), tools=AGENT_TOOLS,
            )
        with open(DB_PATH, "rb") as f:
            db = client.files.upload(file=(DB_PATH.name, f, "application/octet-stream"))
        _resources.update(env_id=env_id, agent_id=agent.id, agent_version=agent.version, db_file_id=db.id)
        atexit.register(_release_files, client)
        return _resources


def _release_files(client):
    file_id = _resources.get("db_file_id")
    if file_id:
        try:
            client.files.delete(file_id)
        except Exception as e:  # noqa: BLE001 - best effort at exit, but say so
            log.warning("could not delete uploaded file %s: %s", file_id, e)


def check_refund(ticket):
    client = make_client()
    res = _ensure_resources(client)
    telemetry.check_budget()
    started = time.perf_counter()
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": res["agent_id"], "version": res["agent_version"]},
        environment_id=res["env_id"],
        resources=[{"type": "file", "file_id": res["db_file_id"], "mount_path": "/customers.db"}],
        title=f"refund {ticket['ticket_id']}",
        metadata={"ticket_id": ticket["ticket_id"], "step": "refund"},
        budget={"type": "limit", "max_list_cost": {"amount": str(CFG["session_budget_cents"]), "currency": "USD"}},
    )
    text, tool_calls = "", 0
    try:
        with client.beta.sessions.events.stream(session_id=session.id) as stream:
            client.beta.sessions.events.send(session_id=session.id, events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": f"Customer ID: {ticket['customer_id']}\n"
                                                     f"Ticket date: {ticket['created_at']}"}],
            }])
            deadline = time.time() + CFG["timeout_s"]
            for event in stream:
                if event.type == "agent.message":
                    text += "".join(b.text for b in event.content if b.type == "text")
                elif event.type == "agent.tool_use":
                    tool_calls += 1
                elif event.type == "session.status_idle" and event.stop_reason.type != "requires_action":
                    break
                elif event.type == "session.status_terminated":
                    break
                if time.time() > deadline:
                    raise TimeoutError(f"refund session {session.id} exceeded {CFG['timeout_s']}s")
    finally:
        _record_and_close(client, session.id, started, tool_calls)
    found = re.findall(r"REFUND_ELIGIBLE:\s*(true|false)", text, re.I)
    if not found:
        raise RuntimeError(f"refund session {session.id} gave no verdict: {text[:200]!r}")
    return found[-1].lower() == "true"


def _record_and_close(client, session_id, started, tool_calls):
    try:
        s = client.beta.sessions.retrieve(session_id)
        usage = s.usage.model_dump() if getattr(s, "usage", None) else {}
        cost = int(((usage.get("list_cost") or {}).get("amount")) or 0) / 100.0
    except Exception as e:  # noqa: BLE001 - telemetry must not mask the real result
        log.warning("could not read usage for session %s: %s", session_id, e)
        usage, cost = {}, 0.0
    telemetry.record_agent_run("managed_agents", SETTINGS["models"]["refund_agent"], cost_usd=cost, usage=usage,
                               turns=None, tool_calls=tool_calls, latency_s=time.perf_counter() - started,
                               extra={"session_id": session_id})
    try:
        if CFG["delete_sessions"]:
            client.beta.sessions.delete(session_id=session_id)
        else:
            client.beta.sessions.archive(session_id=session_id)
    except Exception as e:  # noqa: BLE001
        log.warning("could not close session %s: %s", session_id, e)


def cleanup(apply=False):
    """Delete sessions/environments and archive agents whose names start with NAME_PREFIX."""
    client = make_client()
    for agent in client.beta.agents.list():
        if agent.name.startswith(NAME_PREFIX):
            print(f"archive agent {agent.id} {agent.name}")
            if apply:
                client.beta.agents.archive(agent.id)
    for env in client.beta.environments.list():
        if env.name.startswith(NAME_PREFIX):
            print(f"delete environment {env.id} {env.name}")
            if apply:
                client.beta.environments.delete(env.id)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cleanup", action="store_true")
    ap.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    args = ap.parse_args()
    if args.cleanup:
        cleanup(apply=args.apply)
