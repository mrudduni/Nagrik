"""
ingest_from_jsonl.py
--------------------
Bootstrap ChromaDB from the existing ingestion/data/extracted.jsonl records.
Each record has: name, summary, ministry, department, states, categories, documents, eligibility_rules
We store the summary + eligibility rules as searchable text chunks.
Run from nagrik-agent-backend directory:
    python ../scripts/ingest_from_jsonl.py
"""
import sys
import os
import json
import pathlib
import hashlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "nagrik-agent-backend"))
os.chdir(str(pathlib.Path(__file__).parent.parent / "nagrik-agent-backend"))

from app.rag.store import get_collection

EXTRACTED_JSONL = pathlib.Path("../ingestion/data/extracted.jsonl")

def build_chunk_text(record: dict) -> str:
    """Build searchable text from a scheme record."""
    parts = []

    name = record.get("scheme_name") or ""
    if name:
        parts.append(f"Scheme: {name}")

    ministry = record.get("ministry") or ""
    department = record.get("department") or ""
    if ministry:
        parts.append(f"Ministry: {ministry}")
    if department:
        parts.append(f"Department: {department}")

    summary = record.get("summary") or ""
    if summary:
        parts.append(f"Summary: {summary}")

    categories = record.get("beneficiary_categories") or []
    if categories:
        parts.append(f"Beneficiaries: {', '.join(categories)}")

    states = record.get("applicable_states") or []
    if states:
        parts.append(f"Applicable in: {', '.join(states[:5])}")

    documents = record.get("required_documents") or []
    if documents:
        parts.append(f"Required documents: {', '.join(documents[:8])}")

    rules = record.get("eligibility_rules") or []
    if rules:
        rule_texts = []
        for r in rules:
            if isinstance(r, dict):
                rule_texts.append(f"{r.get('field','')} {r.get('operator','')} {r.get('value','')}")
        if rule_texts:
            parts.append(f"Eligibility: {'; '.join(rule_texts[:5])}")

    return "\n".join(parts)


def main():
    if not EXTRACTED_JSONL.exists():
        print(f"ERROR: {EXTRACTED_JSONL} not found!")
        return

    print(f"Loading records from {EXTRACTED_JSONL}...")
    records = []
    with open(EXTRACTED_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    print(f"Loaded {len(records)} records.")

    collection = get_collection()
    print(f"Collection currently has {collection.count()} items.")

    BATCH_SIZE = 100
    total_added = 0
    skipped = 0

    for batch_start in range(0, len(records), BATCH_SIZE):
        batch = records[batch_start:batch_start + BATCH_SIZE]
        ids, documents, metadatas = [], [], []

        for i, record in enumerate(batch):
            text = build_chunk_text(record)
            if not text.strip():
                skipped += 1
                continue

            raw_id = "|".join([
                record.get("_scheme_id") or record.get("scheme_name") or "unknown",
                str(batch_start + i),
            ])
            chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append({
                "ministry": record.get("ministry") or "",
                "department": record.get("department") or "",
                "scheme": record.get("scheme_name") or "",
                "source_url": record.get("source_url") or "",
                "source_file": record.get("_scheme_id") or "",
                "page": 0,
            })

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            total_added += len(ids)
            print(f"  Ingested batch {batch_start//BATCH_SIZE + 1}: {len(ids)} chunks (total: {total_added})")

    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"  Records processed : {len(records)}")
    print(f"  Chunks ingested   : {total_added}")
    print(f"  Skipped           : {skipped}")
    print(f"  ChromaDB count    : {collection.count()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
