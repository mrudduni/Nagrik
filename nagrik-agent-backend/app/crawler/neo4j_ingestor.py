"""
app/crawler/neo4j_ingestor.py
------------------------------
MERGEs newly discovered schemes from the Tavily crawler into Neo4j.
Uses the same graph schema as the main ingestion pipeline:
  (:Ministry)-[:HAS_DEPARTMENT]->(:Department)-[:OFFERS]->(:Scheme)
  (:Scheme)-[:HAS_RULE]->(:EligibilityRule)
  (:Scheme)-[:REQUIRES]->(:Document)
  (:Scheme)-[:APPLICABLE_IN]->(:State)
  (:Scheme)-[:FOR_CATEGORY]->(:BeneficiaryCategory)

Returns a list of newly ingested scheme IDs (skips existing ones).
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

INGEST_CYPHER = """
MERGE (ministry:Ministry {name: $ministry})
MERGE (dept:Department {name: $department})
MERGE (ministry)-[:HAS_DEPARTMENT]->(dept)
MERGE (s:Scheme {id: $scheme_id})
ON CREATE SET
  s.name          = $name,
  s.summary       = $summary,
  s.source_url    = $source_url,
  s.last_verified = $last_verified,
  s.created_by    = 'tavily_crawler',
  s.is_new        = true,
  s.crawled_at    = $crawled_at
ON MATCH SET
  s.name          = $name,
  s.summary       = $summary,
  s.last_verified = $last_verified
MERGE (dept)-[:OFFERS]->(s)

FOREACH (rule IN $rules |
  MERGE (r:EligibilityRule {scheme_id: $scheme_id, field: rule.field, operator: rule.operator, value: rule.value})
  MERGE (s)-[:HAS_RULE]->(r)
)
FOREACH (doc IN $documents |
  MERGE (d:Document {type: doc})
  MERGE (s)-[:REQUIRES]->(d)
)
FOREACH (state IN $states |
  MERGE (st:State {name: state})
  MERGE (s)-[:APPLICABLE_IN]->(st)
)
FOREACH (cat IN $categories |
  MERGE (bc:BeneficiaryCategory {name: cat})
  MERGE (s)-[:FOR_CATEGORY]->(bc)
)
RETURN s.id AS scheme_id, s.is_new AS is_new
"""

# Returns whether the scheme was brand-new (not already in graph)
CHECK_NEW_CYPHER = """
MATCH (s:Scheme {id: $scheme_id})
RETURN s.created_by = 'tavily_crawler' AS is_crawler_scheme, s.is_new AS is_new
"""


def _make_scheme_id(name: str, source_url: str) -> str:
    """Stable short ID from scheme name + source URL."""
    seed = f"{name.lower().strip()}|{source_url}"
    return "tv-" + hashlib.md5(seed.encode()).hexdigest()[:8]


def ingest_schemes(schemes: list[dict]) -> list[dict]:
    """
    Write all extracted schemes to Neo4j. Returns only the newly created ones
    (those that didn't exist before). Already-existing schemes are skipped.
    """
    from app.rag.neo4j_search import get_driver

    driver = get_driver()
    now = datetime.now(timezone.utc).isoformat()
    newly_ingested = []

    with driver.session() as sess:
        for scheme in schemes:
            name = (scheme.get("name") or "").strip()
            if not name:
                continue

            source_url = scheme.get("source_url", "")
            scheme_id = _make_scheme_id(name, source_url)

            # Check if this scheme already exists in the graph
            existing = sess.run(
                "MATCH (s:Scheme {id: $scheme_id}) RETURN s.id",
                scheme_id=scheme_id,
            ).single()
            if existing:
                logger.debug(f"Skipping existing scheme: {name} ({scheme_id})")
                continue

            rules = []
            for r in (scheme.get("eligibility_rules") or []):
                if isinstance(r, dict) and r.get("field"):
                    rules.append({
                        "field": str(r.get("field", "")),
                        "operator": str(r.get("operator", "eq")),
                        "value": str(r.get("value", "")),
                    })

            documents = [str(d) for d in (scheme.get("documents") or []) if d]
            states = [str(s) for s in (scheme.get("states") or []) if s]
            categories = [str(c) for c in (scheme.get("categories") or []) if c]

            try:
                result = sess.run(
                    INGEST_CYPHER,
                    scheme_id=scheme_id,
                    name=name,
                    summary=scheme.get("summary", ""),
                    source_url=source_url,
                    ministry=scheme.get("ministry") or "Unknown Ministry",
                    department=scheme.get("department") or "Unknown Department",
                    last_verified=now[:10],
                    crawled_at=scheme.get("_crawled_at", now),
                    rules=rules,
                    documents=documents,
                    states=states,
                    categories=categories,
                )
                row = result.single()
                if row:
                    newly_ingested.append({
                        "id": scheme_id,
                        "name": name,
                        "summary": scheme.get("summary", ""),
                        "source_url": source_url,
                        "ministry": scheme.get("ministry", ""),
                        "department": scheme.get("department", ""),
                        "categories": categories,
                        "benefit_type": scheme.get("benefit_type", "Service"),
                        "crawled_at": scheme.get("_crawled_at", now),
                    })
                    logger.info(f"✅ Ingested new scheme: {name} ({scheme_id})")
            except Exception as e:
                logger.error(f"Failed to ingest scheme '{name}': {e}")
                continue

    return newly_ingested
