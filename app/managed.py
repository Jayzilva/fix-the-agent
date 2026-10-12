"""Refund check on Claude Managed Agents."""
import re
import time
import uuid

from app.config import DB_PATH, KB_DIR, SETTINGS, load_prompt, make_client

AGENT_TOOLS = [
    {
        "type": "agent_toolset_20260401",
        "default_config": {"enabled": True, "permission_policy": {"type": "always_allow"}},
        "configs": [
            {"name": "web_fetch", "enabled": False},
            {"name": "web_search", "enabled": False},
        ],
    }
]


def _upload(client, path, mime):
    with open(path, "rb") as f:
        return client.files.upload(file=(path.name, f, mime))


def check_refund(ticket):
    client = make_client()
    run_id = f"{ticket['ticket_id']}-{uuid.uuid4().hex[:8]}"

    environment = client.beta.environments.create(
        name=f"ticketpilot-env-{run_id}",
        config={"type": "cloud", "networking": {"type": "limited"}},
    )
    agent = client.beta.agents.create(
        name=f"ticketpilot-refund-{run_id}",
        model=SETTINGS["models"]["refund_agent"],
        system=load_prompt("refund_agent.md"),
        tools=AGENT_TOOLS,
    )

    resources = []
    for path in sorted(KB_DIR.glob("*.md")):
        uploaded = _upload(client, path, "text/markdown")
        resources.append({"type": "file", "file_id": uploaded.id, "mount_path": f"/kb/{path.name}"})
    db = _upload(client, DB_PATH, "application/octet-stream")
    resources.append({"type": "file", "file_id": db.id, "mount_path": "/customers.db"})

    session = client.beta.sessions.create(
        agent={"type": "agent", "id": agent.id, "version": agent.version},
        environment_id=environment.id,
        resources=resources,
        title=f"Refund check {ticket['ticket_id']}",
    )
    client.beta.sessions.events.send(
        session_id=session.id,
        events=[{
            "type": "user.message",
            "content": [{
                "type": "text",
                "text": f"Ticket date: {ticket['created_at']}\nCustomer ID: {ticket['customer_id']}\n"
                        "Is this customer eligible for a refund?",
            }],
        }],
    )

    deadline = time.time() + 600
    while time.time() < deadline:
        client.beta.sessions.retrieve(session.id)
        events = list(client.beta.sessions.events.list(session.id, order="asc"))
        last_text, done = None, False
        for event in events:
            if event.type == "agent.message":
                last_text = "".join(b.text for b in event.content if b.type == "text")
                done = False
            elif event.type == "session.status_idle" and event.stop_reason.type != "requires_action":
                done = last_text is not None
            elif event.type == "session.status_terminated":
                done = True
        if done:
            found = re.findall(r"REFUND_ELIGIBLE:\s*(true|false)", last_text or "", re.I)
            return bool(found) and found[-1].lower() == "true"
        time.sleep(0.1)
    raise TimeoutError(f"refund session {session.id} did not finish")
