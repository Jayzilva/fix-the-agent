"""Thin helpers around the Claude Messages API."""
import json
import re
import uuid
from datetime import datetime

from app.config import SETTINGS, load_prompt, make_client
from app.kb import full_kb_text

MODEL = SETTINGS["models"]["default"]
MAX_TOKENS = SETTINGS["llm"]["max_tokens"]
EFFORT = SETTINGS["llm"]["effort"]

# Running conversation so the model keeps the context of earlier tickets.
HISTORY = []


def system_prompt():
    return (
        f"Request ID: {uuid.uuid4()}\n"
        f"Current time: {datetime.now().isoformat()}\n\n"
        + load_prompt("base_system.md")
        + "\n\n# Nimbus Cloud knowledge base\n\n"
        + full_kb_text()
    )


def ask(prompt, model=None):
    client = make_client()
    messages = HISTORY + [{"role": "user", "content": prompt}]
    with client.messages.stream(
        model=model or MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt(),
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT},
        messages=messages,
    ) as stream:
        response = stream.get_final_message()
    return "".join(block.text for block in response.content if block.type == "text")


def extract_json(text):
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if match:
        return json.loads(match.group(1))
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


def ask_json(prompt, model=None):
    raw = ask(prompt, model=model)
    fixed = ask(load_prompt("fix_json.md").replace("{raw}", raw), model=model)
    return extract_json(fixed)


def count_words(text):
    answer = ask(
        "Count the number of words in the following text. Reply with only the number.\n\n"
        f"<text>\n{text}\n</text>"
    )
    return int(re.findall(r"\d+", answer)[-1])


def days_between(start, end):
    answer = ask(
        f"How many days are there between {start} and {end}? "
        "Count calendar days. Reply with only the number."
    )
    return int(re.findall(r"-?\d+", answer)[-1])


def lookup_article_id(answer):
    if not answer or str(answer).strip().lower() in ("null", "none", ""):
        return None
    reply = ask(
        "A teammate picked this knowledge base article for a ticket:\n\n"
        f"{answer}\n\n"
        "Using the knowledge base in your instructions, return the exact article ID "
        "(format KB-###) that this refers to. Reply with only the ID, or null if it matches nothing."
    )
    found = re.findall(r"KB-\d{3}", reply)
    return found[-1] if found else None


def write_reply(ticket, fields, feedback=None):
    prompt = load_prompt("writer.md").format(
        ticket=json.dumps(ticket, indent=2),
        fields=json.dumps(fields, indent=2),
        feedback=feedback or "None yet - this is the first draft.",
        word_limit=SETTINGS["pipeline"]["reply_word_limit"],
    )
    text = ask(prompt, model=SETTINGS["models"]["writer"])
    match = re.search(r"<reply>(.*?)</reply>", text, re.S)
    return (match.group(1) if match else text).strip()


def review_reply(ticket, draft):
    prompt = load_prompt("reviewer.md").format(ticket=json.dumps(ticket, indent=2), draft=draft)
    return ask_json(prompt, model=SETTINGS["models"]["reviewer"])


def review_loop(ticket, fields, draft=None):
    limit = SETTINGS["pipeline"]["reply_word_limit"]
    feedback = None
    for _ in range(SETTINGS["pipeline"]["max_review_rounds"]):
        if draft is None or feedback:
            draft = write_reply(ticket, fields, feedback)
        try:
            words = count_words(draft)
            if words > limit:
                feedback = f"The draft has {words} words. It must be at most {limit} words."
                continue
        except:
            pass
        verdict = review_reply(ticket, draft)
        if verdict.get("approved"):
            return draft
        feedback = verdict.get("feedback") or "The draft was not approved."
    return draft


def remember(ticket, result):
    HISTORY.append({"role": "user", "content": f"Ticket:\n{json.dumps(ticket)}"})
    HISTORY.append({"role": "assistant", "content": f"Final triage:\n{json.dumps(result)}"})
