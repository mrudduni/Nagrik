"""
Ingest all government scheme PDFs from data/text_data.

Each PDF filename is treated as the scheme name.

Example:

    Aam Aadmi Bima Yojana.pdf

becomes:

    scheme = "Aam Aadmi Bima Yojana"
"""

import pathlib
import pymupdf

from app.rag.chunker import chunk_document
from app.rag.store import add_chunks

DOCS_ROOT = pathlib.Path("data/text_data")


def ingest_pdf(file_path: pathlib.Path) -> int:
    print(f"\nProcessing: {file_path.name}")

    doc = pymupdf.open(file_path)

    total_chunks = 0

    # The renamed PDF filename is the scheme name.
    scheme_name = file_path.stem

    for page_number, page in enumerate(doc, start=1):

        raw_text = page.get_text().strip()

        if not raw_text:
            continue

        chunks = chunk_document(
            raw_text=raw_text,
            ministry="",
            department="",
            scheme=scheme_name,
            source_file=file_path.name,
            source_url=str(file_path),
            page=page_number,
        )

        total_chunks += add_chunks(chunks)

    doc.close()

    print(
        f"  Extracted {total_chunks} chunks from PDF"
    )

    return total_chunks

def ingest_all() -> int:
    total = 0

    if not DOCS_ROOT.exists():
        print(f"No PDFs found at {DOCS_ROOT}")
        return 0

    pdf_files = list(DOCS_ROOT.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files.")

    for file_path in pdf_files:
        total += ingest_pdf(file_path)

    print("\n" + "=" * 60)
    print(f"TOTAL CHUNKS INGESTED: {total}")
    print("=" * 60)

    return total


if __name__ == "__main__":
    ingest_all()