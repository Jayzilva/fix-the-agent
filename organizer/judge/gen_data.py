"""Generate the TicketPilot dataset (organizer only).

Writes, relative to the repo root:
  data/tickets.jsonl          participant-visible tickets
  data/kb/KB-###.md           knowledge base articles
  data/customers.db           SQLite: plans, customers, charges
  organizer/judge/golden.jsonl  labels (never committed)

Everything is seeded, so re-running produces byte-identical output.

  python organizer/judge/gen_data.py --kb-words 700 --tickets 200
"""
import argparse
import datetime as dt
import json
import random
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from catalog import FEATURE_REQUESTS, KB_TOPICS, OTHER_TOPICS  # noqa: E402

PLANS = [
    # id, name, billing_period, price_usd, refund_window_days
    ("free", "Free", "none", 0, 0),
    ("starter_monthly", "Starter (monthly)", "monthly", 19, 14),
    ("pro_monthly", "Pro (monthly)", "monthly", 49, 14),
    ("pro_annual", "Pro (annual)", "annual", 490, 30),
    ("enterprise_annual", "Enterprise (annual)", "annual", 12000, 0),
]
PLAN_BY_ID = {p[0]: p for p in PLANS}

FIRST = ["Ava", "Liam", "Noah", "Mia", "Zoe", "Ethan", "Priya", "Kenji", "Lucas", "Sara", "Omar", "Elena",
         "Chen", "Fatima", "Jonas", "Amara", "Diego", "Hana", "Ravi", "Ingrid", "Tomas", "Leila", "Marco", "Yuki"]
LAST = ["Silva", "Patel", "Nguyen", "Garcia", "Kowalski", "Okafor", "Smith", "Haddad", "Rossi", "Tanaka",
        "Novak", "Fernando", "Jensen", "Moreau", "Ahmed", "Larsen", "Costa", "Weber", "Kim", "Perera"]
COMPANY_A = ["Blue", "Swift", "Bright", "North", "Iron", "Silver", "Pixel", "Cedar", "Quantum", "Harbor", "Atlas", "Lumen"]
COMPANY_B = ["Labs", "Works", "Analytics", "Health", "Logistics", "Studio", "Retail", "Systems", "Bank", "Media"]
REGIONS = ["us-east", "us-west", "eu-west", "eu-central", "ap-south", "ap-southeast"]
NOTES = [
    "Prefers email contact; finance team in a different timezone than engineering.",
    "Migrated from a competitor last year; uses the CLI heavily in CI pipelines.",
    "Runs a marketing site and two internal APIs; occasional traffic spikes on launches.",
    "Customer success check-in scheduled quarterly; interested in multi-region later.",
    "Small agency managing projects for several of their own clients.",
    "Uses managed Postgres and object storage; asked about SOC 2 report in onboarding.",
    "Startup in growth phase; frequently changes plan size as usage grows.",
    "Has strict procurement process; invoices must include the PO number.",
]

GREETINGS = ["Hi team,", "Hello,", "Hi Nimbus support,", "Hey there,", "Good morning,", "Hi,"]
PROBLEM_OPENERS = ["We noticed that", "Since this morning", "Not sure what changed, but", "Since yesterday",
                   "Quick heads-up:", "Starting today", "For some reason", "Since our last deploy"]
QUESTION_OPENERS = ["Could you tell me", "I was wondering", "Quick question:", "Can you help me understand",
                    "I'd like to know", "Could someone explain"]
CLOSERS = ["Thanks in advance.", "Appreciate the help.", "Thanks!", "Looking forward to your reply.",
           "Cheers.", "Thank you."]
P1_IMPACT = [
    "This has taken our entire production environment down and none of our customers can use our product.",
    "Everything is down for all of our users right now and we are losing revenue every minute.",
    "This is a full production outage affecting every one of our users.",
]
P1_SECURITY = [
    "We believe our account has been compromised and this is an active security incident.",
    "This looks like an active security breach on our account and we need help immediately.",
]
P2_IMPACT = {
    "technical": [
        "Only a couple of people on our team are affected and we have a temporary workaround.",
        "It's blocking one of our workflows, but the rest of the platform works fine.",
        "This affects part of our team; production itself is still running.",
    ],
    "billing": [
        "Please look into this charge and correct it.",
        "We need this billing problem fixed on our account.",
        "Our finance team flagged this and needs it corrected.",
    ],
    "account": [
        "This is blocking me from doing my work, though the rest of the team is fine.",
        "It only affects my user, but I can't get anything done until it's sorted.",
        "One person on our team is stuck because of this.",
    ],
}
P3_PHRASES = ["No urgency, nothing is broken - just looking for guidance.", "Just a question when you get a chance.",
              "Not urgent at all.", "Nothing is broken, I'm just planning ahead."]
FEATURE_WHY = ["Our team would use it every day.", "Several of our developers have asked for this.",
               "It would save us a lot of manual work.", "Competitors already offer something similar."]

FILLER = [
    "This article applies to all Nimbus Cloud workspaces unless a section says otherwise.",
    "Screenshots in the dashboard may differ slightly depending on your plan and region.",
    "If you manage several workspaces, repeat these steps in each workspace that is affected.",
    "Changes made in the dashboard are recorded in the audit log on plans that include audit logging.",
    "Most customers resolve this issue in under fifteen minutes by following the steps below.",
    "Workspace owners and admins can perform every step in this article; other roles may see read-only views.",
    "When contacting support about this topic, include your workspace ID and the approximate time the issue started.",
    "The same behaviour applies to projects created through the API, the CLI and the Terraform provider.",
    "We recommend testing changes in a staging project before applying them to production.",
    "Nimbus Cloud publishes planned maintenance at least five days in advance on the status page.",
    "Some settings take a few minutes to propagate to every region after you save them.",
    "If a step fails, wait a few minutes and try again before escalating, because transient errors clear on their own.",
    "Automation scripts should check for the same conditions described here before retrying an operation.",
    "Keep your CLI up to date, since older versions may show different error messages for the same problem.",
    "Our documentation site has a changelog that lists every behaviour change related to this topic.",
    "Customers on Enterprise plans can ask their technical account manager to review their configuration.",
    "For security reasons support engineers cannot see secret values, passwords or full card numbers.",
    "All timestamps shown in the dashboard use your browser's timezone, while logs and schedules use UTC.",
    "Billing and usage data in the dashboard is refreshed approximately every hour.",
    "Team members who do not have permission to change a setting can still request the change from an admin.",
    "The API exposes the same information shown in the dashboard, so these checks can be scripted.",
    "Community answers on the forum can be helpful, but this article reflects the official behaviour.",
    "If the problem started right after a change, rolling the change back is often the fastest way to confirm the cause.",
    "Please avoid sharing tokens or secrets in support tickets; support will never ask you for them.",
]
FAQ_Q = ["Does this affect all regions?", "Will I lose any data?", "Is there an API for this?",
         "Can support do this for me?", "Does this apply to the Free plan?", "How do I know it worked?"]
FAQ_A = ["Yes, the behaviour is the same in every region.", "No, following these steps does not delete data.",
         "Yes, every dashboard action has an equivalent API endpoint.",
         "Support can help verify the result, but owners and admins usually make the change themselves.",
         "Plan limits may differ, but the steps are the same.",
         "The dashboard shows a confirmation banner and the change appears in the audit log."]


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def write_article(rng, topic, target_words):
    kb_id, category, title, symptom, question, resolution, _ = topic
    parts = [
        f"# {title}",
        f"Article ID: {kb_id} | Category: {category} | Last updated: 2026-08-{rng.randint(1, 28):02d}",
        "## Summary",
        resolution,
    ]
    if symptom:
        parts += ["## Symptoms", f"You may see this when {symptom}."]
    if question:
        parts += ["## Common question", f"Customers often ask {question}."]
    parts += ["## Resolution"]
    for i, sentence in enumerate([s.strip() for s in resolution.split(". ") if s.strip()], 1):
        parts.append(f"{i}. {sentence.rstrip('.')}.")
    parts.append("## Additional notes")
    body_words = sum(len(p.split()) for p in parts)
    notes = []
    pool = FILLER[:]
    while body_words < target_words * 0.8:
        if not pool:
            pool = FILLER[:]
        sentence = pool.pop(rng.randrange(len(pool)))
        notes.append(sentence)
        body_words += len(sentence.split())
        if len(notes) % 5 == 0:
            parts.append(" ".join(notes))
            notes = []
    if notes:
        parts.append(" ".join(notes))
    parts.append("## FAQ")
    for qi in rng.sample(range(len(FAQ_Q)), 4):
        parts.append(f"**{FAQ_Q[qi]}** {FAQ_A[qi]}")
        body_words += 12
    while body_words < target_words:
        sentence = rng.choice(FILLER)
        parts.append(sentence)
        body_words += len(sentence.split())
    parts.append("## Related articles")
    return "\n\n".join(parts) + "\n"


def build_db(rng, path, ticket_customers):
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE plans (id TEXT PRIMARY KEY, name TEXT, billing_period TEXT, price_usd INTEGER);
        CREATE TABLE customers (
            id TEXT PRIMARY KEY, name TEXT, email TEXT, company TEXT, plan_id TEXT REFERENCES plans(id),
            region TEXT, seats INTEGER, signup_date TEXT, notes TEXT);
        CREATE TABLE charges (
            id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(id), amount_usd INTEGER,
            charged_at TEXT, status TEXT, description TEXT);
        """
    )
    con.executemany("INSERT INTO plans VALUES (?,?,?,?)", [p[:4] for p in PLANS])
    charge_no = 0
    total_customers = 900
    for n in range(1, total_customers + 1):
        cid = f"C{n:04d}"
        first, last = rng.choice(FIRST), rng.choice(LAST)
        company = f"{rng.choice(COMPANY_A)} {rng.choice(COMPANY_B)}"
        if cid in ticket_customers:
            plan_id, last_charge = ticket_customers[cid]
        else:
            plan_id = rng.choice([p[0] for p in PLANS])
            last_charge = dt.date(2026, 9, 30) - dt.timedelta(days=rng.randint(1, 300))
        signup = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randint(0, 500))
        con.execute(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, f"{first} {last}", f"{first.lower()}.{last.lower()}@{company.split()[0].lower()}.example",
             company, plan_id, rng.choice(REGIONS), rng.randint(1, 80), signup.isoformat(), rng.choice(NOTES)),
        )
        period = PLAN_BY_ID[plan_id][2]
        if period == "none":
            continue
        step = 30 if period == "monthly" else 365
        count = 5 if period == "monthly" else 2
        for k in range(count):
            when = last_charge - dt.timedelta(days=step * k)
            charge_no += 1
            con.execute(
                "INSERT INTO charges VALUES (?,?,?,?,?,?)",
                (f"ch_{charge_no:05d}", cid, PLAN_BY_ID[plan_id][3], when.isoformat(), "succeeded",
                 f"{PLAN_BY_ID[plan_id][1]} subscription"),
            )
    con.commit()
    con.close()


def pick_refund_case(rng, created):
    """Return (plan_id, last_charge_date, eligible), keeping days well away from window edges."""
    plan_id = rng.choices([p[0] for p in PLANS], weights=[2, 3, 4, 3, 1])[0]
    period, window = PLAN_BY_ID[plan_id][2], PLAN_BY_ID[plan_id][4]
    if period == "none":
        return plan_id, None, False
    want_eligible = window > 0 and rng.random() < 0.55
    if period == "monthly":
        days = rng.randint(1, 9) if want_eligible else rng.randint(19, 28)
    else:
        days = rng.randint(2, 22) if want_eligible else rng.randint(40, 300)
    eligible = window > 0 and days <= window
    return plan_id, created - dt.timedelta(days=days), eligible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb-words", type=int, default=700)
    ap.add_argument("--tickets", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    kb_dir = ROOT / "data" / "kb"
    kb_dir.mkdir(parents=True, exist_ok=True)
    for old in kb_dir.glob("*.md"):
        old.unlink()
    for topic in KB_TOPICS:
        (kb_dir / f"{topic[0]}.md").write_text(write_article(rng, topic, args.kb_words), encoding="utf-8")

    # Unique issues: a problem and a question per ticketable article, plus feature requests and other.
    issues = []
    for topic in KB_TOPICS:
        kb_id, category, title, symptom, question, resolution, allows_p1 = topic
        if not symptom:
            continue
        if kb_id == "KB-054":
            level = "P1"
        elif allows_p1 and category == "technical":
            level = "P1" if rng.random() < 0.4 else "P2"
        else:
            level = "P2"
        issues.append({"key": f"{kb_id}:problem", "kind": "problem", "kb": kb_id, "category": category,
                       "priority": level, "text": symptom, "title": title})
        issues.append({"key": f"{kb_id}:question", "kind": "question", "kb": kb_id, "category": category,
                       "priority": "P3", "text": question, "title": title})
    for i, feat in enumerate(FEATURE_REQUESTS):
        issues.append({"key": f"FR-{i:02d}", "kind": "feature", "kb": None, "category": "feature_request",
                       "priority": "P3", "text": feat, "title": f"Feature request: {feat}"})
    for i, other in enumerate(OTHER_TOPICS):
        issues.append({"key": f"OT-{i:02d}", "kind": "other", "kb": None, "category": "other",
                       "priority": "P3", "text": other, "title": other.split(".")[0][:60]})

    chosen = list(issues)
    rng.shuffle(chosen)
    chosen = chosen[: min(len(chosen), int(args.tickets * 0.62))]
    while len(chosen) < args.tickets:
        chosen.append(rng.choice(chosen[: int(args.tickets * 0.62)]))
    rng.shuffle(chosen)

    tickets, golden, ticket_customers = [], [], {}
    customer_ids = rng.sample(range(1, 901), args.tickets)
    seen = set()
    for n, issue in enumerate(chosen, 1):
        tid = f"T{n:04d}"
        cid = f"C{customer_ids[n - 1]:04d}"
        created = dt.date(2026, 9, 1) + dt.timedelta(days=rng.randint(0, 29))
        plan_id, last_charge, eligible = pick_refund_case(rng, created)
        ticket_customers[cid] = (plan_id, last_charge or created)
        name = f"{rng.choice(FIRST)}"
        if issue["kind"] == "problem":
            impact = (rng.choice(P1_SECURITY) if issue["kb"] == "KB-054" else rng.choice(P1_IMPACT)) \
                if issue["priority"] == "P1" else rng.choice(P2_IMPACT[issue["category"]])
            body = f"{rng.choice(GREETINGS)}\n\n{rng.choice(PROBLEM_OPENERS)} {issue['text']}. {impact}\n\n{rng.choice(CLOSERS)}\n{name}"
            subject = rng.choice([issue["title"], cap(issue["text"].split(",")[0])[:70], f"Problem: {issue['title'].lower()}"])
        elif issue["kind"] == "question":
            body = f"{rng.choice(GREETINGS)}\n\n{rng.choice(QUESTION_OPENERS)} {issue['text']}? {rng.choice(P3_PHRASES)}\n\n{rng.choice(CLOSERS)}\n{name}"
            subject = rng.choice([f"Question about {issue['title'].lower()}", issue["title"], "Quick question"])
        elif issue["kind"] == "feature":
            body = f"{rng.choice(GREETINGS)}\n\nIt would be great if Nimbus Cloud offered {issue['text']}. {rng.choice(FEATURE_WHY)} Not urgent, just a suggestion.\n\n{rng.choice(CLOSERS)}\n{name}"
            subject = rng.choice(["Feature idea", "Suggestion", f"Request: {issue['text']}"])
        else:
            body = f"{rng.choice(GREETINGS)}\n\n{issue['text']}\n\n{rng.choice(CLOSERS)}\n{name}"
            subject = rng.choice(["Hello from a fellow company", "Inquiry", issue["title"]])
        tickets.append({"ticket_id": tid, "customer_id": cid, "created_at": created.isoformat(),
                        "subject": subject, "body": body})
        golden.append({"ticket_id": tid, "category": issue["category"], "priority": issue["priority"],
                       "kb_article_id": issue["kb"], "refund_eligible": eligible, "issue_key": issue["key"],
                       "is_near_duplicate": issue["key"] in seen, "plan_id": plan_id,
                       "last_charge": last_charge.isoformat() if last_charge else None})
        seen.add(issue["key"])

    (ROOT / "data").mkdir(exist_ok=True)
    with open(ROOT / "data" / "tickets.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for t in tickets:
            f.write(json.dumps(t) + "\n")
    with open(HERE / "golden.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for g in golden:
            f.write(json.dumps(g) + "\n")
    build_db(rng, ROOT / "data" / "customers.db", ticket_customers)

    dupes = sum(g["is_near_duplicate"] for g in golden)
    kb_words = sum(len(p.read_text(encoding="utf-8").split()) for p in kb_dir.glob("*.md"))
    print(f"tickets={len(tickets)} near_duplicates={dupes} ({dupes / len(tickets):.0%}) "
          f"refund_true={sum(g['refund_eligible'] for g in golden)} kb_articles={len(KB_TOPICS)} kb_words={kb_words}")


if __name__ == "__main__":
    main()
