"""
ChromaDB wrapper for Tree-RAG storage. Uses a local persistent client so
the demo doesn't depend on network access to a hosted vector DB.
"""
from app.config import settings
from app.rag.chunker import DocChunk
import hashlib  

_COLLECTION_NAME = "nagrik_gov_docs"

_client = None
_embedding_fn = None


def _get_client():

    global _client

    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )

    return _client


def _get_embedding_fn():

    global _embedding_fn

    if _embedding_fn is None:
        from chromadb.utils import embedding_functions

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

    ids = []

    for i, c in enumerate(chunks):
        raw_id = "|".join([
        c.scheme or "unknown",
        c.source_file or "",
        str(c.page or 0),
        str(i),
        c.text[:200],
        ])

    chunk_id = hashlib.sha256(
        raw_id.encode("utf-8")
    ).hexdigest()

    ids.append(chunk_id)

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
