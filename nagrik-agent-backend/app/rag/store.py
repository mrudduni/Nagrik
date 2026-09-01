"""
ChromaDB wrapper for Tree-RAG storage. Uses a local persistent client so
the demo doesn't depend on network access to a hosted vector DB.
"""
import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from app.rag.chunker import DocChunk


_COLLECTION_NAME = "nagrik_gov_docs"

_client = None
_embedding_fn = None


def _get_client():

    global _client

    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )

    return _client


def _get_embedding_fn():

    global _embedding_fn

    if _embedding_fn is None:

        _embedding_fn = (
            embedding_functions
            .SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

    return _embedding_fn


def get_collection():

    return _get_client().get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_get_embedding_fn(),
    )




def add_chunks(chunks: list[DocChunk]) -> int:
    if not chunks:
        return 0

    collection = get_collection()

    ids = [
        f"{c.scheme or 'unknown'}-{c.page or 0}-{i}"
        for i, c in enumerate(chunks)
    ]

    documents = [c.text for c in chunks]

    metadatas = [
        {
            "ministry": c.ministry,
            "department": c.department,
            "scheme": c.scheme or "",
            "source_url": c.source_url or "",
            "source_file": c.source_file or "",
            "page": c.page or 0,
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return len(chunks)


def query(
    text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> dict:

    collection = get_collection()

    return collection.query(
        query_texts=[text],
        n_results=n_results,
        where=where if where else None,
        include=["documents", "metadatas", "distances"],
    )