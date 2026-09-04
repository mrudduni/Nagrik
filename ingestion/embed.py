"""
ingestion/embed.py
------------------
Step 4: Generate embeddings for each Scheme node's summary and store
        them as `embedding` vector properties. Also creates the vector index.

Uses: sentence-transformers all-MiniLM-L6-v2 (384-dim, local, free)

Usage:
    python ingestion/embed.py [--batch-size 64]
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── Neo4j ─────────────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ── Cypher ────────────────────────────────────────────────────────────────────
CREATE_VECTOR_INDEX = f"""
CREATE VECTOR INDEX scheme_embeddings IF NOT EXISTS
FOR (s:Scheme) ON (s.embedding)
OPTIONS {{
  indexConfig: {{
    `vector.dimensions`: {EMBEDDING_DIM},
    `vector.similarity_function`: 'cosine'
  }}
}}
"""

FETCH_SCHEMES = """
MATCH (s:Scheme)
WHERE s.summary IS NOT NULL AND s.summary <> ''
RETURN s.id AS id, s.summary AS summary
"""

SET_EMBEDDING = """
MATCH (s:Scheme {id: $scheme_id})
SET s.embedding = $embedding
"""

SET_EMBEDDING_BATCH = """
UNWIND $items AS item
MATCH (s:Scheme {id: item.id})
SET s.embedding = item.embedding
"""



def create_index(session):
    try:
        session.run(CREATE_VECTOR_INDEX)
        print("[embed] Vector index `scheme_embeddings` created/confirmed ✅")
    except Exception as e:
        print(f"[embed] Index warning (may already exist): {e}")


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=64,
                        help="Number of schemes to embed at once (default: 64)")
    args = parser.parse_args()

    print(f"[embed] Loading model: {MODEL_NAME} …", flush=True)
    model = SentenceTransformer(MODEL_NAME)
    print(f"[embed] Model loaded. Embedding dim: {EMBEDDING_DIM}", flush=True)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("[embed] Connected to Neo4j ✅", flush=True)
    except Exception as e:
        sys.exit(f"❌  Cannot connect to Neo4j: {e}")

    with driver.session() as session:
        # Create the vector index first
        create_index(session)

        # Fetch all schemes
        result = session.run(FETCH_SCHEMES)
        rows = [(r["id"], r["summary"]) for r in result]

    print(f"[embed] Found {len(rows)} schemes to embed.", flush=True)

    batch_size = args.batch_size
    total_batches = (len(rows) + batch_size - 1) // batch_size

    with driver.session() as session:
        for batch_idx in range(total_batches):
            batch = rows[batch_idx * batch_size: (batch_idx + 1) * batch_size]
            ids = [b[0] for b in batch]
            texts = [b[1] for b in batch]

            embeddings = model.encode(texts, batch_size=batch_size,
                                      show_progress_bar=False, normalize_embeddings=True)

            items = [
                {"id": scheme_id, "embedding": emb.tolist()}
                for scheme_id, emb in zip(ids, embeddings)
            ]
            session.run(SET_EMBEDDING_BATCH, items=items)

            print(f"  [embed] Batch {batch_idx + 1}/{total_batches} done "
                  f"({min((batch_idx + 1) * batch_size, len(rows))}/{len(rows)})", flush=True)

    print(f"\n[embed] ✅ Embeddings stored for {len(rows)} schemes.", flush=True)
    driver.close()


if __name__ == "__main__":
    main()
