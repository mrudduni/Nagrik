"""
populate_neo4j.py
-----------------
One-shot: load all 1,297 schemes from decode/ingestion/data/extracted.jsonl
into Neo4j Aura and generate vector embeddings.

Run from the Nagrik folder:
    python scripts/populate_neo4j.py
"""
import json
import sys
import pathlib
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j credentials ────────────────────────────────────────────────────────
NEO4J_URI      = os.environ.get("NEO4J_URI", "neo4j+s://50580f6d.databases.neo4j.io")
NEO4J_USER     = os.environ.get("NEO4J_USER", os.environ.get("NEO4J_USERNAME", "50580f6d"))
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

CACHE_FILE = pathlib.Path(__file__).parent.parent.parent / "decode" / "ingestion" / "data" / "extracted.jsonl"
NOW_ISO = datetime.now(timezone.utc).isoformat()

CONSTRAINTS = [
    "CREATE CONSTRAINT scheme_id_unique IF NOT EXISTS FOR (s:Scheme) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT ministry_name_unique IF NOT EXISTS FOR (m:Ministry) REQUIRE m.name IS UNIQUE",
    "CREATE CONSTRAINT department_name_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT state_name_unique IF NOT EXISTS FOR (st:State) REQUIRE st.name IS UNIQUE",
    "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:BeneficiaryCategory) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT document_type_unique IF NOT EXISTS FOR (doc:Document) REQUIRE doc.type IS UNIQUE",
]

UNIFIED_INGEST_CYPHER = """
MERGE (ministry:Ministry {name: $ministry})
MERGE (dept:Department {name: $department})
MERGE (ministry)-[:HAS_DEPARTMENT]->(dept)
MERGE (s:Scheme {id: $scheme_id})
SET   s.name=$name, s.summary=$summary, s.source_url=$source_url, s.last_verified=$last_verified
MERGE (dept)-[:OFFERS]->(s)
FOREACH (rule IN $rules |
  MERGE (r:EligibilityRule {scheme_id:$scheme_id, field:rule.field, operator:rule.operator, value:rule.value})
  MERGE (s)-[:HAS_RULE]->(r)
)
FOREACH (doc IN $documents | MERGE (d:Document {type: doc}) MERGE (s)-[:REQUIRES]->(d))
FOREACH (st IN $states | MERGE (state:State {name: st}) MERGE (s)-[:APPLICABLE_IN]->(state))
FOREACH (cat IN $categories | MERGE (c:BeneficiaryCategory {name: cat}) MERGE (s)-[:FOR_CATEGORY]->(c))
"""


def ingest_record(session, rec):
    scheme_id = rec.get("_scheme_id") or rec.get("scheme_id", "")
    if not scheme_id:
        scheme_id = (rec.get("scheme_name") or "unknown").lower().replace(" ", "-")[:64]
    session.run(
        UNIFIED_INGEST_CYPHER,
        ministry=(rec.get("ministry") or "Unknown Ministry").strip() or "Unknown Ministry",
        department=(rec.get("department") or "Unknown Department").strip() or "Unknown Department",
        scheme_id=scheme_id,
        name=(rec.get("scheme_name") or scheme_id).strip(),
        summary=(rec.get("summary") or "").strip(),
        source_url=(rec.get("source_url") or "").strip(),
        last_verified=NOW_ISO,
        rules=[{"field":r.get("field","").strip(),"operator":r.get("operator","eq").strip(),"value":str(r.get("value","")).strip()} for r in (rec.get("eligibility_rules") or []) if r.get("field","").strip()],
        documents=[d.strip() for d in (rec.get("required_documents") or []) if d.strip()],
        states=[s.strip() for s in (rec.get("applicable_states") or []) if s.strip()],
        categories=[c.strip() for c in (rec.get("beneficiary_categories") or []) if c.strip()],
    )
    return scheme_id


def main():
    if not CACHE_FILE.exists():
        sys.exit(f"ERROR: {CACHE_FILE} not found!")

    from neo4j import GraphDatabase
    print("\n[1/3] Connecting to Neo4j Aura...", flush=True)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("      Connected!", flush=True)

    with driver.session() as s:
        for c in CONSTRAINTS:
            try: s.run(c)
            except: pass
    print("[1/3] Constraints applied.", flush=True)

    # Load records
    print(f"\n[2/3] Loading {CACHE_FILE.name}...", flush=True)
    records = []
    with open(CACHE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: records.append(json.loads(line))
                except: pass
    print(f"      {len(records)} records loaded.", flush=True)

    scheme_ids = []
    with driver.session() as session:
        for i, rec in enumerate(records, 1):
            try:
                sid = ingest_record(session, rec)
                scheme_ids.append(sid)
            except Exception as e:
                print(f"  Error record {i}: {e}", flush=True)
            if i % 100 == 0 or i == len(records):
                print(f"  {i}/{len(records)} ingested", flush=True)

    with driver.session() as session:
        for label in ["Ministry","Department","Scheme","EligibilityRule","Document","State","BeneficiaryCategory"]:
            cnt = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
            print(f"  {label}: {cnt}")

    # Embeddings
    print("\n[3/3] Building vector embeddings...", flush=True)
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers", "-q"])
        from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    pairs = []
    for rec in records:
        sid = rec.get("_scheme_id") or rec.get("scheme_id") or (rec.get("scheme_name","").lower().replace(" ","-")[:64])
        text = " ".join(filter(None,[rec.get("scheme_name",""),rec.get("summary","")," ".join(rec.get("beneficiary_categories") or [])," ".join((rec.get("applicable_states") or [])[:3])]))
        if sid and text.strip():
            pairs.append((sid, text.strip()))

    print(f"  Embedding {len(pairs)} schemes...", flush=True)
    embeddings = model.encode([p[1] for p in pairs], batch_size=64, show_progress_bar=True, normalize_embeddings=True)

    # Create vector index
    with driver.session() as session:
        try:
            session.run("""CREATE VECTOR INDEX scheme_embeddings IF NOT EXISTS
                FOR (s:Scheme) ON s.embedding
                OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}""")
            print("  Vector index created.", flush=True)
        except Exception as e:
            print(f"  Index note: {e}", flush=True)

    # Store embeddings
    for i in range(0, len(pairs), 50):
        batch = pairs[i:i+50]
        embs  = embeddings[i:i+50]
        with driver.session() as session:
            for (sid, _), emb in zip(batch, embs):
                session.run("MATCH (s:Scheme {id:$id}) SET s.embedding=$emb", id=sid, emb=emb.tolist())
        if (i//50+1) % 5 == 0 or i+50 >= len(pairs):
            print(f"  Stored {min(i+50,len(pairs))}/{len(pairs)} embeddings", flush=True)

    with driver.session() as session:
        cnt = session.run("MATCH (s:Scheme) WHERE s.embedding IS NOT NULL RETURN count(s) AS c").single()["c"]
        print(f"\n  Schemes with embeddings: {cnt}")

    driver.close()
    print("\nDone! Neo4j Aura is fully populated.", flush=True)


if __name__ == "__main__":
    main()
