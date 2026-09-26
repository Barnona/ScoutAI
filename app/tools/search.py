"""Direct SerpApi search wrapper used by ScoutAI."""

import serpapi

from config.settings import MAX_SOURCES, SERPAPI_API_KEY


def web_search(query: str, engine: str = "google_light") -> list[dict]:
    """Search the web through SerpApi and return compact source records."""
    if not SERPAPI_API_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not configured.")

    client = serpapi.Client(api_key=SERPAPI_API_KEY, timeout=15)
    results = client.search({
        "engine": engine,
        "q": query,
        "hl": "en",
        "gl": "in",
    })

    sources = []
    for item in (results.get("organic_results", []) or [])[:MAX_SOURCES]:
        sources.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source": item.get("source", ""),
        })

    return sources
