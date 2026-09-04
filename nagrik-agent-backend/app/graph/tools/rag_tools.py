"""
LangChain tools wrapping Neo4j knowledge graph search.
Replaces the old ChromaDB-based tree_rag_search entirely.

The Neo4j backend provides:
  - Semantic vector search (all-MiniLM-L6-v2 embeddings)
  - Graph context enrichment (rules, docs, states, beneficiary categories)
  - No local files, no ephemeral storage — works on any deployment
"""
from langchain_core.tools import tool
from app.rag.neo4j_search import hybrid_search, format_for_rag


@tool
def tree_rag_search(
    query: str,
    ministry: str | None = None,
    department: str | None = None,
    scheme: str | None = None,
) -> dict:
    """Search the government scheme knowledge graph for information about
    Indian government welfare schemes, eligibility, benefits, documents, and
    application procedures. Uses Neo4j vector search + graph traversal.

    Call this for ANY factual question about government schemes or policies.
    Optionally pass ministry/department/scheme to narrow the search.

    Returns matched schemes with eligibility rules, required documents, states,
    beneficiary categories, and source URLs.
    """
    # Build enriched query with optional filters
    search_query = query
    if scheme:
        search_query = f"{scheme} {query}"
    elif ministry:
        search_query = f"{ministry} {query}"
    elif department:
        search_query = f"{department} {query}"

    results = hybrid_search(search_query, top_k=5)

    if not results:
        return {
            "found": False,
            "chunks": [],
            "text": "No matching government schemes found in the knowledge base.",
            "sources": [],
        }

    text = format_for_rag(results)
    sources = [
        {
            "scheme": r.get("scheme_name", ""),
            "ministry": r.get("ministry", ""),
            "department": r.get("department", ""),
            "source_url": r.get("source_url", ""),
            "score": round(r.get("score", 0), 4),
        }
        for r in results
    ]

    return {
        "found": True,
        "chunks": results,
        "text": text,
        "sources": sources,
    }


RAG_TOOLS = [tree_rag_search]
