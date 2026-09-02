"""
Hybrid Tree-RAG retrieval.

Retrieval strategy:
1. Apply explicit ministry/department/scheme filters when provided.
2. Detect a strong scheme-name match from the query.
3. If an exact/strong scheme match exists, retrieve only that scheme.
4. Otherwise use hybrid vector + keyword retrieval.
5. Deduplicate duplicate PDFs/schemes so one scheme does not dominate results.
"""

import re
import unicodedata

from app.config import settings
from app.rag import store


def _normalize(text: str) -> str:
    """
    Normalize English/Hindi/Hinglish text without deleting Unicode letters.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", str(text)).lower()

    # Fix common mojibake/encoding artifacts.
    replacements = {
        "â€œ": " ",
        "â€": " ",
        "â€™": "'",
        "â€“": "-",
        "â€”": "-",
        "ï»¿": " ",
        "Â": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Keep Unicode letters/numbers and whitespace.
    text = "".join(
        char if (char.isalnum() or char.isspace()) else " "
        for char in text
    )

    return " ".join(text.split())


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def _keyword_score(
    query: str,
    scheme: str | None,
    text: str,
) -> float:
    """
    Keyword score used together with vector similarity.

    Scheme-name matches receive much higher weight than ordinary
    text matches.
    """
    normalized_query = _normalize(query)
    normalized_scheme = _normalize(scheme or "")
    normalized_text = _normalize(text)

    if not normalized_query:
        return 0.0

    score = 0.0

    # Very strong signal: complete query appears in scheme name.
    if normalized_query in normalized_scheme:
        score += 20.0

    query_words = _tokens(normalized_query)

    stop_words = {
        # English
        "what",
        "is",
        "the",
        "a",
        "an",
        "about",
        "tell",
        "me",
        "of",
        "for",
        "to",
        "and",
        "on",
        "in",
        "this",
        "that",
        "which",
        "how",
        "can",
        "i",
        "get",
        # Common scheme words
        "scheme",
        "yojana",
        "yojna",
        "benefits",
        "benefit",
        "eligibility",
        "eligible",
        "apply",
        "application",
        "documents",
        # Hindi/Hinglish
        "kya",
        "hai",
        "hain",
        "ke",
        "ki",
        "ka",
        "ko",
        "se",
        "mein",
        "yeh",
        "ye",
        "batao",
        "iske",
        "iske",
        "liye",
    }

    query_words = {
        word
        for word in query_words
        if word not in stop_words and len(word) > 1
    }

    if not query_words:
        return score

    scheme_words = _tokens(normalized_scheme)
    text_words = _tokens(normalized_text)

    scheme_matches = query_words & scheme_words
    text_matches = query_words & text_words

    score += len(scheme_matches) * 4.0
    score += len(text_matches) * 0.5

    # Strong partial scheme-name coverage.
    if query_words and scheme_words:
        coverage = len(query_words & scheme_words) / len(query_words)

        if coverage >= 0.8:
            score += 12.0
        elif coverage >= 0.5:
            score += 6.0

    return score


def _scheme_match_score(query: str, scheme: str | None) -> float:
    """
    Measure how strongly the query identifies a specific scheme.
    Returns a score from 0 to 1.
    """

    normalized_query = _normalize(query)
    normalized_scheme = _normalize(scheme or "")

    if not normalized_query or not normalized_scheme:
        return 0.0

    # Direct phrase match.
    if normalized_scheme in normalized_query:
        return 1.0

    query_words = set(normalized_query.split())
    scheme_words = set(normalized_scheme.split())

    stop_words = {
        # English question words
        "what", "is", "the", "a", "an", "about",
        "tell", "me", "of", "for", "to", "and",
        "on", "in", "this", "that", "which",
        "how", "can", "i",

        # Scheme-question words
        "scheme", "schemes",
        "yojana", "yojna",
        "benefit", "benefits",
        "eligibility", "eligible",
        "apply", "application",
        "documents", "document",
        "details", "information",

        # Hinglish
        "kya", "hai", "hain", "ke", "ki", "ka",
        "ko", "se", "mein", "yeh", "ye",
        "batao", "iske", "liye",
    }

    meaningful_query_words = {
        word
        for word in query_words
        if word not in stop_words and len(word) > 1
    }

    if not meaningful_query_words:
        return 0.0

    matched_words = (
        meaningful_query_words & scheme_words
    )

    coverage = (
        len(matched_words)
        / len(meaningful_query_words)
    )

    return coverage


def _find_strong_scheme_match(
    query: str,
    candidates: list[dict],
) -> str | None:
    """
    Find the strongest scheme represented in retrieved candidates.

    A scheme is considered an explicit match when most of the
    meaningful words in the query identify that scheme.
    """

    best_scheme = None
    best_score = 0.0

    for candidate in candidates:
        scheme = candidate.get("scheme")

        if not scheme:
            continue

        score = _scheme_match_score(query, scheme)

        if score > best_score:
            best_score = score
            best_scheme = scheme

    # Strong scheme-name coverage.
    if best_score >= 0.60:
        return best_scheme

    return None


def _deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    """
    Keep only the best chunk for each canonical scheme.
    Duplicate PDFs such as:
        Scheme.pdf
        Scheme (2).pdf
    are treated as the same scheme.
    """

    best_by_scheme = {}

    for chunk in chunks:
        scheme_key = _canonical_scheme(
            chunk.get("scheme")
        )

        if not scheme_key:
            scheme_key = _normalize(
                chunk.get("source_file") or ""
            )

        existing = best_by_scheme.get(scheme_key)

        if existing is None:
            best_by_scheme[scheme_key] = chunk
            continue

        # Keep the chunk with the better hybrid score.
        if chunk["hybrid_score"] > existing["hybrid_score"]:
            best_by_scheme[scheme_key] = chunk

    return sorted(
        best_by_scheme.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )
def _build_candidate(
    query: str,
    doc: str,
    meta: dict,
    distance,
) -> dict:
    vector_score = (
        1.0 - distance
        if distance is not None
        else 0.0
    )

    keyword_score = _keyword_score(
        query=query,
        scheme=meta.get("scheme"),
        text=doc,
    )

    return {
        "text": doc,
        "ministry": meta.get("ministry"),
        "department": meta.get("department"),
        "scheme": meta.get("scheme"),
        "source_file": meta.get("source_file"),
        "source_url": meta.get("source_url"),
        "page": meta.get("page"),
        "distance": distance,
        "vector_score": vector_score,
        "keyword_score": keyword_score,
        "hybrid_score": vector_score + keyword_score,
    }

def tree_rag_search(
    query: str,
    ministry: str | None = None,
    department: str | None = None,
    scheme: str | None = None,
) -> dict:
    """
    Search the government-scheme knowledge base.

    Exact/strong scheme queries are restricted to the matched scheme.
    General queries use hybrid retrieval across schemes.
    """

    if not query or not query.strip():
        return {
            "found": False,
            "chunks": [],
            "message": "Please provide a question or search query.",
        }

    where = {}

    if ministry:
        where["ministry"] = ministry

    if department:
        where["department"] = department

    if scheme:
        where["scheme"] = scheme

    # ---------------------------------------------------------
    # STEP 1: Initial broad retrieval
    # ---------------------------------------------------------

    result = store.query(
        text=query,
        n_results=settings.rag_candidate_k,
        where=where or None,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = (
        result.get("distances", [[]])[0]
        if "distances" in result
        else [None] * len(documents)
    )

    if not documents:
        return {
            "found": False,
            "chunks": [],
            "message": "No relevant information found in the knowledge base.",
        }

    candidates = [
        _build_candidate(
            query=query,
            doc=doc,
            meta=meta,
            distance=distance,
        )
        for doc, meta, distance in zip(
            documents,
            metadatas,
            distances,
        )
    ]

    # ---------------------------------------------------------
    # STEP 2: Explicit scheme argument
    # ---------------------------------------------------------

    if scheme:
        candidates = [
            c
            for c in candidates
            if _normalize(c.get("scheme") or "")
            == _normalize(scheme)
        ]

    # ---------------------------------------------------------
    # STEP 3: Detect strong scheme-name match
    # ---------------------------------------------------------

    if not scheme:
        matched_scheme = _find_strong_scheme_match(
            query,
            candidates,
        )

        if matched_scheme:
            # Retrieve again using the exact scheme metadata.
            exact_result = store.query(
                text=query,
                n_results=settings.rag_candidate_k,
                where={
                    "scheme": matched_scheme,
                    **(
                        {"ministry": ministry}
                        if ministry
                        else {}
                    ),
                    **(
                        {"department": department}
                        if department
                        else {}
                    ),
                },
            )

            exact_documents = exact_result.get(
                "documents",
                [[]],
            )[0]

            exact_metadatas = exact_result.get(
                "metadatas",
                [[]],
            )[0]

            exact_distances = exact_result.get(
                "distances",
                [[]],
            )[0]

            candidates = [
                _build_candidate(
                    query=query,
                    doc=doc,
                    meta=meta,
                    distance=distance,
                )
                for doc, meta, distance in zip(
                    exact_documents,
                    exact_metadatas,
                    exact_distances,
                )
            ]

            # Safety check: only keep the matched scheme.
            candidates = [
                c
                for c in candidates
                if _normalize(c.get("scheme") or "")
                == _normalize(matched_scheme)
            ]

    # ---------------------------------------------------------
    # STEP 4: Rank
    # ---------------------------------------------------------

    candidates.sort(
        key=lambda chunk: chunk["hybrid_score"],
        reverse=True,
    )

    candidates = _deduplicate_chunks(candidates)

    if not candidates:
        return {
            "found": False,
            "chunks": [],
            "message": "No sufficiently relevant information found.",
        }

    # ---------------------------------------------------------
    # STEP 5: Relevance check
    # ---------------------------------------------------------

    best = candidates[0]

    vector_relevant = (
        best["distance"] is not None
        and best["distance"]
        <= settings.rag_similarity_distance_threshold
    )

    keyword_relevant = best["keyword_score"] >= 1.5

    if not vector_relevant and not keyword_relevant:
        return {
            "found": False,
            "chunks": [],
            "message": "No sufficiently relevant information found.",
        }

    return {
        "found": True,
        "chunks": candidates[: settings.rag_top_k],
    }

def _canonical_scheme(scheme: str | None) -> str:
    if not scheme:
        return ""

    normalized = _normalize(scheme)

    # Remove duplicate-copy suffixes:
    # "Scheme (2)" -> "Scheme"
    # "Scheme (3)" -> "Scheme"
    # etc.
    normalized = re.sub(r"\s+\(\d+\)\s*$", "", normalized)

    return normalized.strip()