"""Knowledge base access. Articles are parsed once per process and kept in memory."""
import functools
import re

from app.config import KB_DIR


def _section(text, heading):
    match = re.search(rf"^## {heading}\n\n(.+?)(?=\n## |\Z)", text, re.S | re.M)
    return match.group(1).strip() if match else ""


@functools.lru_cache(maxsize=1)
def load_articles():
    articles = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = re.search(r"Category: (\w+)", text)
        articles.append({
            "id": path.stem,
            "title": text.splitlines()[0].lstrip("# ").strip(),
            "category": meta.group(1) if meta else "",
            "summary": _section(text, "Summary"),
            "symptom": _section(text, "Symptoms").removeprefix("You may see this when ").rstrip("."),
            "question": _section(text, "Common question").removeprefix("Customers often ask ").rstrip("."),
            "body": text,
        })
    return tuple(articles)


@functools.lru_cache(maxsize=1)
def article_ids():
    return frozenset(a["id"] for a in load_articles())


def get_article(article_id):
    for article in load_articles():
        if article["id"] == article_id:
            return article
    return None


@functools.lru_cache(maxsize=1)
def kb_index():
    """Compact index of every article: id, category, title, the issue it covers and its resolution.

    About 6k tokens for 60 articles (vs ~65k for the full text). It is static, so it sits in the
    cached system prompt and is billed at the cache-read rate after the first call.
    """
    lines = []
    for a in load_articles():
        issue = "; ".join(s for s in (a["symptom"], a["question"]) if s)
        lines.append(f"{a['id']} [{a['category']}] {a['title']}\n  Covers: {issue}\n  Resolution: {a['summary']}")
    return "\n".join(lines)


def keyword_search(query, limit=3):
    words = [w for w in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(w) > 2]
    scored = []
    for article in load_articles():
        haystack = " ".join((article["summary"], article["symptom"], article["question"])).lower()
        title = article["title"].lower()
        score = sum(haystack.count(w) + 5 * title.count(w) for w in words)
        if score:
            scored.append((score, article))
    scored.sort(key=lambda pair: -pair[0])
    return [a for _, a in scored[:limit]]
