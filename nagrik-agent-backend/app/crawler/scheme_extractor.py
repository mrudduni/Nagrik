"""
app/crawler/scheme_extractor.py
---------------------------------
Uses Gemini (via get_llm) to extract structured scheme data from raw
webpage text returned by Tavily. Returns a list of ExtractedScheme dicts.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a government scheme data extractor. Given raw webpage text from an official \
Indian government website, extract ALL government schemes mentioned.

For each scheme, return a JSON object with these exact fields:
- name: Full official name of the scheme (string)
- summary: 2-3 sentence description of what the scheme offers (string)
- ministry: Administering ministry (string, or "Unknown Ministry")
- department: Administering department (string, or "Unknown Department")
- categories: List of beneficiary categories (e.g. ["Farmers", "Women", "Students"])
- eligibility_rules: List of objects with {{field, operator, value}}
  - field: short snake_case identifier (e.g. "income", "age", "caste")
  - operator: one of "lt", "gt", "lte", "gte", "eq", "in"
  - value: the threshold or accepted value (string)
- documents: List of required document names (strings)
- states: List of applicable state names (empty list if central/all-India)
- benefit_type: One of "Cash Transfer", "Subsidy", "Insurance", "Loan", "Service", "Pension", "Scholarship"
- benefit_amount: Numeric amount if mentioned (null if not mentioned)
- source_url: The official URL for this scheme (use the page URL provided)
- level: "Central" if central government, "State" if state government

Return ONLY a JSON array (starting with [ and ending with ]). No explanation, no markdown.
If no distinct scheme is found, return [].

Page URL: {url}
Page Title: {title}

Page Content (may be long):
{content}
"""


def extract_schemes_from_page(
    url: str,
    title: str,
    content: str,
) -> list[dict]:
    """
    Call Gemini to extract structured scheme data from one page's raw text.
    Returns a list of scheme dicts (may be empty if nothing found).
    """
    from app.llm.get_llm import get_llm

    # Trim content to avoid token overload (~8000 chars ≈ ~2000 tokens)
    content_trimmed = content[:8000] if len(content) > 8000 else content

    prompt = EXTRACTION_PROMPT.format(
        url=url,
        title=title,
        content=content_trimmed,
    )

    try:
        llm = get_llm(temperature=0.1)
        response = llm.invoke(prompt)
        content_obj = getattr(response, "content", response)
        if isinstance(content_obj, list):
            raw_text = "".join(
                part if isinstance(part, str) else (part.get("text", "") if isinstance(part, dict) else str(part))
                for part in content_obj
            )
        else:
            raw_text = str(content_obj)
    except Exception as e:
        logger.error(f"LLM extraction failed for {url}: {e}")
        return []

    # Parse JSON from response
    try:
        # Try to find JSON array in response
        json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if json_match:
            schemes = json.loads(json_match.group())
        else:
            schemes = json.loads(raw_text.strip())
        if not isinstance(schemes, list):
            return []
        return [s for s in schemes if isinstance(s, dict) and s.get("name")]
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON from LLM for {url}: {e}\nRaw: {raw_text[:500]}")
        return []


def extract_schemes_from_pages(pages: list[dict]) -> list[dict]:
    """
    Batch-extract schemes from a list of Tavily result pages.
    Returns flat list of all extracted scheme dicts with source metadata attached.
    """
    all_schemes = []
    for page in pages:
        url = page.get("url", "")
        title = page.get("title", "")
        content = page.get("content", "")
        if not content.strip():
            continue

        logger.info(f"Extracting schemes from: {url}")
        schemes = extract_schemes_from_page(url, title, content)

        # Attach source metadata
        for s in schemes:
            if not s.get("source_url"):
                s["source_url"] = url
            s["_crawled_at"] = page.get("crawled_at", "")
            s["_tavily_score"] = page.get("score", 0.0)

        all_schemes.extend(schemes)
        logger.info(f"  → Extracted {len(schemes)} scheme(s)")

    return all_schemes
