"""
app/crawler/tavily_crawler.py
-----------------------------
Uses Tavily Search API to discover newly announced Indian government schemes
from official domains only. Returns raw text chunks ready for LLM extraction.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

OFFICIAL_DOMAINS = [
    "myscheme.gov.in",
    "pib.gov.in",
    "india.gov.in",
    "pmjay.gov.in",
    "pmkisan.gov.in",
    "niti.gov.in",
    "mospi.gov.in",
    "pmgsy.nic.in",
    "pmegp.kvic.gov.in",
]

SEARCH_QUERIES = [
    "new central government welfare scheme launched 2024 2025",
    "pradhan mantri yojana scheme eligibility benefits apply",
    "state government scheme subsidy farmers women education",
    "new pension scholarship housing scheme ministry india",
    "msme startup scheme loan subsidy india",
]


def _get_client():
    """Lazy-load Tavily client to avoid import error if key not set."""
    from tavily import TavilyClient
    from app.config import settings
    if not settings.tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY is not set in environment.")
    return TavilyClient(api_key=settings.tavily_api_key)


def search_new_schemes(
    max_results_per_query: int = 5,
    queries: Optional[list[str]] = None,
) -> list[dict]:
    """
    Run multiple targeted Tavily searches on official government domains.
    Returns a deduplicated list of result dicts with keys:
      url, title, content, score, query
    """
    client = _get_client()
    queries = queries or SEARCH_QUERIES
    seen_urls: set[str] = set()
    results: list[dict] = []

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                include_domains=OFFICIAL_DOMAINS,
                max_results=max_results_per_query,
                include_raw_content=True,
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                results.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "content": r.get("raw_content") or r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "query": query,
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            logger.warning(f"Tavily search failed for query '{query}': {e}")
            continue

    logger.info(f"Tavily crawler found {len(results)} unique pages.")
    return results


def stable_id_from_url(url: str) -> str:
    """Derive a stable scheme ID from its source URL (short MD5 prefix)."""
    return "tv-" + hashlib.md5(url.encode()).hexdigest()[:8]
