"""
Tavily-based search and extraction tools for the retrieval agent.
These tools are bound to the LLM in the autonomous retrieval node.

IMPORTANT: Groq API requires tool message content to be a string.
All tool return values MUST be JSON strings, not raw dicts/lists.
"""

from __future__ import annotations

import json
from langchain_core.tools import tool
from langchain_tavily import TavilySearch, TavilyExtract

from config import MAX_SEARCH_RESULTS


@tool
def tavily_search(query: str) -> str:
    """Search the web for information on a given query.
    Returns a JSON string of results with title, content, and URL.
    Use this to find diverse sources on a research sub-question.

    Args:
        query: The search query string. Be specific and varied in your queries.
    """
    search = TavilySearch(
        max_results=MAX_SEARCH_RESULTS,
        search_depth="advanced",
        include_raw_content=False,
    )
    try:
        results = search.invoke({"query": query})
        # Normalize output format
        if isinstance(results, list):
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", "Untitled"),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "domain": _extract_domain(r.get("url", "")),
                })
            return json.dumps(formatted)
        elif isinstance(results, str):
            return results
        return json.dumps([])
    except Exception as e:
        return json.dumps([{"error": str(e), "title": "Search Error", "content": "", "url": "", "domain": ""}])


@tool
def tavily_extract(url: str) -> str:
    """Extract the full content from a specific URL.
    Use this when you need deeper content from a promising source found via search.

    Args:
        url: The URL to extract content from.
    """
    extract = TavilyExtract()
    try:
        result = extract.invoke({"urls": [url]})
        if isinstance(result, dict) and "results" in result:
            results = result["results"]
            if results:
                return json.dumps({
                    "url": url,
                    "content": results[0].get("raw_content", ""),
                    "title": results[0].get("title", "Untitled"),
                })
        return json.dumps({"url": url, "content": "Could not extract content", "title": ""})
    except Exception as e:
        return json.dumps({"url": url, "content": f"Extraction error: {str(e)}", "title": ""})


def _extract_domain(url: str) -> str:
    """Extract domain from URL for diversity tracking."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return "unknown"


# List of all tools available to the retrieval agent
RETRIEVAL_TOOLS = [tavily_search, tavily_extract]
