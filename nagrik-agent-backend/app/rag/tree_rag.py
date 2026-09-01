"""
Hybrid Tree-RAG retrieval.

Retrieval strategy:
1. Apply ministry/department filters when provided.
2. Search using vector similarity.
3. Boost chunks whose scheme name/title matches words in the query.
4. Prefer exact scheme-name matches over semantically similar schemes.
5. Return "not found" when nothing is sufficiently relevant.
"""

import re

from torch import dist
from app.rag import store


SIMILARITY_DISTANCE_THRESHOLD = 0.90


def _normalize(text: str) -> str:
    """Normalize text for robust keyword matching."""

    text = text.lower()

    # Remove common PDF/encoding garbage.
    text = text.replace("â€œ", " ")
    text = text.replace("â€", " ")
    text = text.replace("ï»¿", " ")
    text = text.replace("Â", " ")

    # Replace punctuation with spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return " ".join(text.split())


def _keyword_score(query: str, scheme: str | None, text: str) -> float:
    """
    Score lexical relevance.

    Exact phrase matches in the scheme name receive the
    strongest boost, followed by individual scheme words.
    """

    normalized_query = _normalize(query)
    normalized_scheme = _normalize(scheme or "")
    normalized_text = _normalize(text)

    if not normalized_query:
        return 0.0

    score = 0.0

    # ---------------------------------------------------------
    # Exact phrase match
    # ---------------------------------------------------------

    if normalized_query in normalized_scheme:
        score += 10.0

    # ---------------------------------------------------------
    # Important phrase: remove common question words
    # ---------------------------------------------------------

    stop_words = {
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
        "scheme",
        "yojana",
        "scholarship",
    }

    query_words = [
        word
        for word in normalized_query.split()
        if word not in stop_words
    ]

    scheme_words = set(normalized_scheme.split())
    text_words = set(normalized_text.split())

    if not query_words:
        return score

    # ---------------------------------------------------------
    # Scheme-name word matches
    # ---------------------------------------------------------

    scheme_matches = set(query_words) & scheme_words

    score += len(scheme_matches) * 3.0

    # ---------------------------------------------------------
    # Text matches
    # ---------------------------------------------------------

    text_matches = set(query_words) & text_words

    score += len(text_matches) * 0.5

    return score

def tree_rag_search(
    query: str,
    ministry: str | None = None,
    department: str | None = None,
) -> dict:

    # ---------------------------------------------------------
    # 1. Hierarchical metadata filtering
    # ---------------------------------------------------------

    where = {}

    if ministry:
        where["ministry"] = ministry

    if department:
        where["department"] = department

    # ---------------------------------------------------------
    # 2. Vector search
    # ---------------------------------------------------------

    result = store.query(
        text=query,
        n_results=10,
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

    # ---------------------------------------------------------
    # 3. Build candidates
    # ---------------------------------------------------------

    candidates = []

    for doc, meta, distance in zip(
        documents,
        metadatas,
        distances,
    ):

        scheme = meta.get("scheme", "")

        keyword_score = _keyword_score(
            query=query,
            scheme=scheme,
            text=doc,
        )

        # Lower vector distance = better.
        #
        # Convert it into a simple similarity-like score.
        vector_score = (
            1.0 - distance
            if distance is not None
            else 0.0
        )

        # Hybrid score.
        hybrid_score = vector_score + keyword_score

        candidates.append({
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
            "hybrid_score": hybrid_score,
        })

    # ---------------------------------------------------------
    # 4. Rank by hybrid score
    # ---------------------------------------------------------

    candidates.sort(
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # 5. Relevance check
    # ---------------------------------------------------------

    best = candidates[0]

    # Accept if:
    # - vector similarity is reasonably good, OR
    # - the query strongly matches the scheme name.
    vector_relevant = (
        best["distance"] is not None
        and best["distance"] <= SIMILARITY_DISTANCE_THRESHOLD
    )

    scheme_relevant = best["keyword_score"] >= 1.5

    if not vector_relevant and not scheme_relevant:
        return {
            "found": False,
            "chunks": [],
            "message": "No sufficiently relevant information found.",
        }

    # ---------------------------------------------------------
    # 6. Return top results
    # ---------------------------------------------------------

    return {
        "found": True,
        "chunks": candidates[:5],
    }