"""
LangChain tool wrapping Tree-RAG retrieval over government scheme/policy
documents.
"""
from langchain_core.tools import tool
from app.rag.retriever import tree_rag_search as _tree_rag_search


@tool
def tree_rag_search(
    query: str,
    ministry: str | None = None,
    department: str | None = None,
    scheme: str | None = None,
) -> dict:
    """Search government scheme/policy knowledge base. Optionally filter
    by ministry/department/scheme for more precise hierarchical retrieval.
    Returns matched chunks with source citations, or an explicit
    'not found' result rather than a fabricated answer."""
    return _tree_rag_search(
        query=query,
        ministry=ministry,
        department=department,
        scheme=scheme,
    )


RAG_TOOLS = [tree_rag_search]
