"""
Hierarchy-aware chunking for government documents.

Each chunk carries metadata (ministry, department, scheme, source_url) so
retrieval can filter hierarchically (Ministry -> Department -> Scheme)
before falling back to pure vector similarity — this is the "Tree" in
Tree-RAG.
"""

from dataclasses import dataclass, field


@dataclass
class DocChunk:
    text: str
    ministry: str
    department: str
    scheme: str | None = None
    source_url: str | None = None
    source_file: str | None = None
    page: int | None = None
    metadata: dict = field(default_factory=dict)


def chunk_document(
    raw_text: str,
    ministry: str,
    department: str,
    scheme: str | None = None,
    source_url: str | None = None,
    source_file: str | None = None,
    page: int | None = None,
    max_chunk_chars: int = 800,
    overlap: int = 100,
) -> list[DocChunk]:

    chunks: list[DocChunk] = []

    text = raw_text.strip()

    if not text:
        return chunks

    start = 0

    while start < len(text):
        end = start + max_chunk_chars
        piece = text[start:end]

        chunks.append(
            DocChunk(
                text=piece,
                ministry=ministry,
                department=department,
                scheme=scheme,
                source_url=source_url,
                source_file=source_file,
                page=page,
            )
        )

        start = end - overlap if end - overlap > start else end

    return chunks