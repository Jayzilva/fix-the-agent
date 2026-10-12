from claude_agent_sdk import tool

from app.kb import keyword_search, load_articles, to_html


def _text(value):
    return {"content": [{"type": "text", "text": value}]}


@tool("search_kb", "Search for stuff in the docs.", {"type": "object", "properties": {"query": {}}})
async def search_kb(args):
    hits = keyword_search(args.get("query"), limit=5)
    return _text("\n\n".join(to_html(a["body"]) for a in hits) or "No results")


@tool("find_article", "Finds an article.", {"type": "object", "properties": {"query": {}}})
async def find_article(args):
    hits = keyword_search(args.get("query"), limit=10)
    return _text("\n".join(f"{a['id']}: {a['title']}" for a in hits) or "No results")


@tool("lookup_docs", "Look up documentation.", {"type": "object", "properties": {"q": {}}})
async def lookup_docs(args):
    hits = keyword_search(args.get("q"), limit=3)
    return _text("\n\n---\n\n".join(a["body"] for a in hits) or "No results")


@tool("get_article", "Gets an article.", {"type": "object", "properties": {"id": {}}})
async def get_article(args):
    for article in load_articles():
        if article["id"] == str(args.get("id")).strip():
            return _text(to_html(article["body"]))
    return _text("Not found")


@tool("list_articles", "Lists articles.", {"type": "object", "properties": {}})
async def list_articles(args):
    return _text("\n".join(f"{a['id']}: {a['title']}" for a in load_articles()))


KB_TOOLS = [search_kb, find_article, lookup_docs, get_article, list_articles]
