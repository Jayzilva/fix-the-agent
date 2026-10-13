"""Run TicketPilot over every ticket and write out/results.jsonl."""
import argparse
import asyncio
import json
import logging

from app import orchestrator, telemetry
from app.config import OUTPUT_PATH, SETTINGS, TICKETS_PATH
from app.pipeline import process_ticket

log = logging.getLogger("ticketpilot")


def load_tickets():
    with open(TICKETS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


async def main(limit=None, only=None, concurrency=None):
    tickets = load_tickets()
    if only:
        tickets = [t for t in tickets if t["ticket_id"] in only]
    if limit:
        tickets = tickets[:limit]

    semaphore = asyncio.Semaphore(concurrency or SETTINGS["pipeline"]["concurrency"])
    failures = 0

    async def one(ticket):
        nonlocal failures
        async with semaphore:
            try:
                result = await process_ticket(ticket)
            except telemetry.BudgetExceeded:
                raise
            except Exception:
                failures += 1
                log.exception("%s failed", ticket["ticket_id"])
                return None
            log.info("%s done  $%.5f", ticket["ticket_id"], telemetry.ticket_cost(ticket["ticket_id"]))
            return result

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = await asyncio.gather(*(one(t) for t in tickets))
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for result in results:
            if result is not None:
                out.write(json.dumps(result) + "\n")
    await orchestrator.close()
    done = len(tickets) - failures
    print(f"Done: {done}/{len(tickets)} tickets, ${telemetry.run_cost():.4f} total "
          f"(${telemetry.run_cost() / max(done, 1):.5f}/ticket). Results: {OUTPUT_PATH}")
    print("Telemetry report: python scripts/telemetry_report.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triage Nimbus Cloud support tickets.")
    parser.add_argument("--limit", type=int, help="only process the first N tickets")
    parser.add_argument("--only", nargs="*", help="only process these ticket IDs")
    parser.add_argument("--concurrency", type=int, help="tickets in flight (default: settings)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main(limit=args.limit, only=args.only, concurrency=args.concurrency))
