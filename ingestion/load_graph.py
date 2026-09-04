"""
ingestion/load_graph.py
-----------------------
Step 3: Read extracted.jsonl and build the Neo4j knowledge graph.

Schema:
  (:Ministry {name})-[:HAS_DEPARTMENT]->(:Department {name})
    -[:OFFERS]->(:Scheme {id, name, summary, source_url, last_verified})
      -[:HAS_RULE]->(:EligibilityRule {field, operator, value})
      -[:REQUIRES]->(:Document {type})
      -[:APPLICABLE_IN]->(:State {name})
      -[:FOR_CATEGORY]->(:BeneficiaryCategory {name})

All operations use MERGE so re-running is idempotent.

Usage:
    python ingestion/load_graph.py
"""

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
CACHE_FILE = pathlib.Path(__file__).parent / "data" / "extracted.jsonl"

# ── Neo4j ─────────────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

NOW_ISO = datetime.now(timezone.utc).isoformat()


# ── Constraints / indexes ─────────────────────────────────────────────────────
CONSTRAINTS = [
    "CREATE CONSTRAINT scheme_id_unique IF NOT EXISTS FOR (s:Scheme) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT ministry_name_unique IF NOT EXISTS FOR (m:Ministry) REQUIRE m.name IS UNIQUE",
    "CREATE CONSTRAINT department_name_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT state_name_unique IF NOT EXISTS FOR (st:State) REQUIRE st.name IS UNIQUE",
    "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:BeneficiaryCategory) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT document_type_unique IF NOT EXISTS FOR (doc:Document) REQUIRE doc.type IS UNIQUE",
]


def apply_constraints(driver):
    with driver.session() as session:
        for cypher in CONSTRAINTS:
            try:
                session.run(cypher)
            except Exception as e:
                pass
    print("[load_graph] Constraints verified.", flush=True)



# ── Single unified Cypher query per scheme ────────────────────────────────────
UNIFIED_INGEST_CYPHER = """
MERGE (ministry:Ministry {name: $ministry})
MERGE (dept:Department {name: $department})
MERGE (ministry)-[:HAS_DEPARTMENT]->(dept)

MERGE (s:Scheme {id: $scheme_id})
SET   s.name          = $name,
      s.summary       = $summary,
      s.source_url    = $source_url,
      s.last_verified = $last_verified

MERGE (dept)-[:OFFERS]->(s)

FOREACH (rule IN $rules |
  MERGE (r:EligibilityRule {
      scheme_id: $scheme_id,
      field:     rule.field,
      operator:  rule.operator,
      value:     rule.value
  })
  MERGE (s)-[:HAS_RULE]->(r)
)

FOREACH (doc IN $documents |
  MERGE (d:Document {type: doc})
  MERGE (s)-[:REQUIRES]->(d)
)

FOREACH (st IN $states |
  MERGE (state:State {name: st})
  MERGE (s)-[:APPLICABLE_IN]->(state)
)

FOREACH (cat IN $categories |
  MERGE (c:BeneficiaryCategory {name: cat})
  MERGE (s)-[:FOR_CATEGORY]->(c)
)
"""


def ingest_record(session, rec: dict):
    scheme_id = rec.get("_scheme_id") or rec.get("scheme_id", "")
    if not scheme_id:
        return

    ministry = (rec.get("ministry") or "Unknown Ministry").strip() or "Unknown Ministry"
    department = (rec.get("department") or "Unknown Department").strip() or "Unknown Department"
    name = (rec.get("scheme_name") or scheme_id).strip()
    summary = (rec.get("summary") or "").strip()
    source_url = (rec.get("source_url") or "").strip()

    rules = [
        {
            "field": r.get("field", "").strip(),
            "operator": r.get("operator", "eq").strip(),
            "value": str(r.get("value", "")).strip(),
        }
        for r in (rec.get("eligibility_rules") or [])
        if r.get("field", "").strip()
    ]
    documents = [d.strip() for d in (rec.get("required_documents") or []) if d.strip()]
    states = [s.strip() for s in (rec.get("applicable_states") or []) if s.strip()]
    categories = [c.strip() for c in (rec.get("beneficiary_categories") or []) if c.strip()]

    session.run(
        UNIFIED_INGEST_CYPHER,
        ministry=ministry,
        department=department,
        scheme_id=scheme_id,
        name=name,
        summary=summary,
        source_url=source_url,
        last_verified=NOW_ISO,
        rules=rules,
        documents=documents,
        states=states,
        categories=categories,
    )



def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if not CACHE_FILE.exists():
        sys.exit(f"❌  {CACHE_FILE} not found. Run extract.py first.")

    records = []
    with open(CACHE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    print(f"[load_graph] Loaded {len(records)} extracted records.", flush=True)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("[load_graph] Connected to Neo4j ✅", flush=True)
    except Exception as e:
        sys.exit(f"❌  Cannot connect to Neo4j: {e}")

    apply_constraints(driver)

    with driver.session() as session:
        for i, rec in enumerate(records, 1):
            try:
                ingest_record(session, rec)
            except Exception as e:
                print(f"  [load_graph] Error on record {i}: {e}", flush=True)
            if i % 50 == 0 or i == len(records):
                print(f"  [load_graph] Ingested {i}/{len(records)} schemes …", flush=True)

    print(f"[load_graph] ✅ Done. {len(records)} schemes loaded into Neo4j.", flush=True)

    # Print node counts
    with driver.session() as session:
        labels = ["Ministry", "Department", "Scheme", "EligibilityRule",
                  "Document", "State", "BeneficiaryCategory"]
        print("\n[load_graph] Node counts:")
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            cnt = result.single()["cnt"]
            print(f"  {label}: {cnt}")

    driver.close()


if __name__ == "__main__":
    main()
