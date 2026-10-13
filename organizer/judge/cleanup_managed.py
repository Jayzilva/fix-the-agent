"""Clean up Managed Agents resources left behind by TicketPilot runs (organizer only).

Deletes sessions, environments and the uploaded KB/DB files, and archives agents, whose names/titles start with
the TicketPilot prefixes. Archiving an agent is permanent. Dry run unless --apply is given.

  python organizer/judge/cleanup_managed.py           # list what would be cleaned
  python organizer/judge/cleanup_managed.py --apply   # do it
"""
import argparse
import re

import anthropic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    client = anthropic.Anthropic(base_url="https://api.anthropic.com")

    sessions = [s for s in client.beta.sessions.list() if (s.title or "").startswith("Refund check ")]
    envs = [e for e in client.beta.environments.list() if e.name.startswith("ticketpilot-env-")]
    agents = [a for a in client.beta.agents.list() if a.name.startswith("ticketpilot-refund-")
              and not getattr(a, "archived_at", None)]
    files = [f for f in client.files.list() if re.fullmatch(r"KB-\d{3}\.md|customers\.db", f.filename or "")]
    print(f"sessions={len(sessions)} environments={len(envs)} agents={len(agents)} uploaded_files={len(files)}")
    if not args.apply:
        print("Dry run. Re-run with --apply to delete sessions/environments and archive agents.")
        return
    for s in sessions:
        try:
            client.beta.sessions.delete(session_id=s.id)
        except anthropic.APIStatusError as e:
            print(f"session {s.id}: {e.status_code}")
    for e in envs:
        try:
            client.beta.environments.delete(e.id)
        except anthropic.APIStatusError as err:
            print(f"environment {e.id}: {err.status_code}")
    for a in agents:
        try:
            client.beta.agents.archive(a.id)
        except anthropic.APIStatusError as err:
            print(f"agent {a.id}: {err.status_code}")
    for f in files:
        try:
            client.files.delete(f.id)
        except anthropic.APIStatusError as err:
            print(f"file {f.id}: {err.status_code}")
    print("done")


if __name__ == "__main__":
    main()
