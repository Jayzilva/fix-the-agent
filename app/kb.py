import re

from app.config import KB_DIR


def load_articles():
    articles = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        articles.append({"id": path.stem, "title": title, "body": text})
    return articles


def full_kb_text():
    return "\n\n---\n\n".join(a["body"] for a in load_articles())


def to_html(markdown):
    html = []
    for block in markdown.split("\n\n"):
        block = block.strip()
        if block.startswith("## "):
            html.append(f"<h2>{block[3:]}</h2>")
        elif block.startswith("# "):
            html.append(f"<h1>{block[2:]}</h1>")
        elif re.match(r"^\d+\. ", block):
            items = "".join(f"<li>{line.split('. ', 1)[1]}</li>" for line in block.splitlines())
            html.append(f"<ol>{items}</ol>")
        else:
            block = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", block)
            html.append(f"<p>{block}</p>")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Nimbus Help Center</title>"
        "<link rel='stylesheet' href='https://help.nimbus.example/assets/main.css'></head>"
        "<body><div class='container'><nav class='breadcrumbs'><a href='/'>Help Center</a></nav>"
        f"<article class='kb-article'>{''.join(html)}</article>"
        "<footer><p>Was this article helpful? <a href='#'>Yes</a> <a href='#'>No</a></p>"
        "<p>&copy; 2026 Nimbus Cloud, Inc. All rights reserved.</p></footer></div></body></html>"
    )


def keyword_search(query, limit=60):
    words = [w for w in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(w) > 2]
    scored = []
    for article in load_articles():
        haystack = article["body"].lower()
        title = article["title"].lower()
        score = sum(haystack.count(w) + 10 * title.count(w) for w in words)
        if score:
            scored.append((score, article))
    scored.sort(key=lambda pair: -pair[0])
    return [a for _, a in scored[:limit]]
