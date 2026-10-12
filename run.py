"""Run TicketPilot over every ticket and write out/results.jsonl."""
import argparse
import asyncio
import json

from app import orchestrator
from app.config import OUTPUT_PATH, TICKETS_PATH
from app.pipeline import process_ticket


def load_tickets():
    with open(TICKETS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


async def main(limit=None, only=None):
    tickets = load_tickets()
    if only:
        tickets = [t for t in tickets if t["ticket_id"] in only]
    if limit:
        tickets = tickets[:limit]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for ticket in tickets:
            print(f"Processing {ticket['ticket_id']}...")
            try:
                result = await process_ticket(ticket)
                out.write(json.dumps(result) + "\n")
                out.flush()
            except:
                pass
    await orchestrator.close()
    print(f"Done. Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triage Nimbus Cloud support tickets.")
    parser.add_argument("--limit", type=int, help="only process the first N tickets")
    parser.add_argument("--only", nargs="*", help="only process these ticket IDs")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, only=args.only))
