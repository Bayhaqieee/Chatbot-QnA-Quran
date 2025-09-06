from __future__ import annotations
import re
import requests
from typing import Dict, Any
import config

# Tiered search routing logic
_WIKIPEDIA_PATTERNS = [
    r"\b(history of|sejarah)\b", r"\b(who was|siapakah)\b", r"\b(when did|kapan)\b",
    r"\b(biography of|biografi)\b", r"\b(battle of|perang)\b", r"event"
]

def _route_query(query: str) -> str:
    """Routes query to either Wikipedia or SearxNG based on patterns."""
    q = (query or "").lower()
    if any(re.search(pat, q) for pat in _WIKIPEDIA_PATTERNS):
        return "wikipedia"
    return "searxng"

def _trim_text(s: str, limit: int = 600) -> str:
    s = (s or "").strip()
    return s if len(s) <= limit else s[:limit - 1] + "…"

# Search provider functions
def wikipedia_search(query: str, num: int = 3, timeout: int = 8) -> Dict[str, Any]:
    """Queries MediaWiki API."""
    lang = config.WIKIPEDIA_LANG
    headers = {'User-Agent': 'IslamicQnA-Agent/1.0'}
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "utf8": 1, "format": "json"},
            timeout=timeout, headers=headers
        )
        r.raise_for_status()
        data = r.json()
        hits = (data.get("query", {}).get("search", []))[:num]
        normalized = []
        for h in hits:
            title = h.get("title", "")
            url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            snippet = re.sub('<[^<]+?>', '', h.get("snippet", ""))
            normalized.append({"title": title, "url": url, "snippet": _trim_text(snippet), "provider": "wikipedia"})
        return {"normalized": normalized}
    except Exception as e:
        print(f"Wikipedia search failed: {e}")
        return {"normalized": []}

def searxng_search(query: str, num: int = 5, timeout: int = 10) -> Dict[str, Any]:
    """Queries the self-hosted SearxNG JSON API using a POST request."""
    headers = {"User-Agent": "IslamicQnA-Agent/1.0", "Accept": "application/json"}
    # UPDATED: Using a POST request can be more reliable for avoiding blocks
    params = {
        "q": query, "format": "json", "engines": config.SEARXNG_ENGINES, "language": config.WIKIPEDIA_LANG
    }
    try:
        r = requests.post(config.SEARXNG_ENDPOINT, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        results = (data.get("results", []))[:num]
        norm_items = [{"title": _trim_text(it.get("title")), "url": it.get("url", ""), "snippet": _trim_text(it.get("content")), "provider": "searxng"} for it in results]
        return {"normalized": norm_items}
    except Exception as e:
        print(f"SearxNG search failed: {e}")
        return {"normalized": []}

# Main tool function (unchanged)
def tiered_web_search(query: str) -> str:
    """Performs a tiered web search and returns a formatted string for the agent."""
    route = _route_query(query)
    pkg = {}
    if route == "wikipedia":
        pkg = wikipedia_search(query)
        if not pkg.get("normalized"):
            pkg = searxng_search(query)
    else:
        pkg = searxng_search(query)
        if not pkg.get("normalized"):
            pkg = wikipedia_search(query)

    output_str = ""
    if pkg.get("normalized"):
        for item in pkg["normalized"]:
            output_str += f"Title: {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}\n\n"
    else:
        output_str += "No results found from web search."
        
    return output_str