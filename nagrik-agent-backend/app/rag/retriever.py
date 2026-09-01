"""
Tree-RAG retrieval: filter hierarchically by ministry/department metadata
when provided, then rank by vector similarity within that subset. Falls
back to pure vector search across everything if no filter is given.

Returns an explicit "not found" rather than letting the LLM hallucinate
when nothing relevant is in the store — this is checked in the demo test
suite (see tests/test_rag.py).
"""
from app.rag import store

SIMILARITY_DISTANCE_THRESHOLD = 0.85  # tune against real data; chroma default metric is L2/cosine-ish


def tree_rag_search(
    query: str,
    ministry: str | None = None,
    department: str | None = None,
    scheme: str | None = None,
) -> dict:
    where = {}
    if ministry:
        where["ministry"] = ministry
    if department:
        where["department"] = department
    if scheme:
        where["scheme"] = scheme

    result = store.query(text=query, n_results=5, where=where or None)

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0] if "distances" in result else [None] * len(documents)

    if not documents:
        return {"found": False, "chunks": [], "message": "No relevant information found in the knowledge base."}

    chunks = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        if dist is not None and dist > SIMILARITY_DISTANCE_THRESHOLD:
            continue
        chunks.append({
            "text": doc,
            "ministry": meta.get("ministry"),
            "department": meta.get("department"),
            "scheme": meta.get("scheme"),
            "source_url": meta.get("source_url"),
            "page": meta.get("page"),
            "distance": dist,
        })

    if not chunks:
        return {"found": False, "chunks": [], "message": "No sufficiently relevant information found."}

    return {"found": True, "chunks": chunks}
