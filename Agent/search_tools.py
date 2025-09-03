from __future__ import annotations
import re
import requests
from typing import List, Dict, Any
import json
import config

# Helpers
_BASIC_PATTERNS = [
    r"^\s*what\s+is\b", r"^\s*apa\s+itu\b",
    r"\bdefinition\b", r"\bdefine\b", r"\bpengertian\b",
    r"\bwhat\s+does\s+.*\bmean\b"
]

def _classify(query: str) -> str:
    q = (query or "").lower()
    for pat in _BASIC_PATTERNS:
        if re.search(pat, q):
            return "basic"
    return "intermediate"

def _trim_text(s: str, limit: int = 600) -> str:
    s = (s or "").strip()
    return s if len(s) <= limit else s[:limit - 1] + "…"

# Providers
def wikipedia_search(query: str, num: int = 5, timeout: int = 8) -> Dict[str, Any]:
    """Query MediaWiki; returns {'normalized': [...], 'raw': {...}}."""
    lang = getattr(config, "WIKIPEDIA_LANG", "en")
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "utf8": 1, "format": "json"},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        hits = ((data.get("query") or {}).get("search") or [])[:num]
        normalized = []
        for h in hits:
            title = h.get("title", "")
            url = f"https://{lang}.wikipedia.org/wiki/" + title.replace(" ", "_")
            snippet = (h.get("snippet", "")
                       .replace('<span class="searchmatch">', '')
                       .replace('</span>', ''))
            normalized.append({
                "title": title, "url": url, "snippet": _trim_text(snippet), "provider": "wikipedia"
            })
        return {"normalized": normalized, "raw": {"hits": hits}}
    except Exception as e:
        print(f"Wikipedia search failed: {e}")
        return {"normalized": [], "raw": {"error": "wikipedia_fetch_failed"}}

def searxng_search(query: str, num: int = 8, timeout: int = 10) -> Dict[str, Any]:
    """Query SearxNG JSON API; returns {'normalized': [...], 'raw': {...}}."""
    headers = {"User-Agent": "islamic-qna-client", "Accept": "application/json"}
    try:
        r = requests.get(
            config.SEARXNG_ENDPOINT,
            params={
                "q": query, "format": "json", "engines": config.SEARXNG_ENGINES,
                "language": config.WIKIPEDIA_LANG, "safesearch": 1
            },
            headers=headers, timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        results = (data.get("results") or [])[:num]
        norm_items = [{"title": _trim_text(it.get("title")), "url": it.get("url", ""), "snippet": _trim_text(it.get("content")), "provider": "searxng"} for it in results]
        return {"normalized": norm_items, "raw": data}
    except Exception as e:
        print(f"SearxNG search failed: {e}")
        return {"normalized": [], "raw": {"error": "searxng_fetch_failed"}}

# Public API
def tiered_web_search(query: str, k_basic: int = 5, k_adv: int = 8) -> str:
    """Performs a tiered web search and returns a formatted string."""
    level = _classify(query)
    pkg = {}
    if level == "basic":
        pkg = wikipedia_search(query, num=k_basic)
        if not pkg.get("normalized"):
            pkg = searxng_search(query, num=k_adv)
    else:
        pkg = searxng_search(query, num=k_adv)
        if not pkg.get("normalized"):
            pkg = wikipedia_search(query, num=k_basic)
            
    # Format the normalized results into a single string for the agent
    output_str = f"Search Level: {level}\n\n"
    if pkg.get("normalized"):
        for item in pkg["normalized"]:
            output_str += f"Title: {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}\nProvider: {item['provider']}\n\n"
    else:
        output_str += "No results found."
        
    return output_str