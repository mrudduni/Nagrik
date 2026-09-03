"""
api/graph.py
------------
Neo4j driver singleton and all Cypher query helpers used by the endpoints.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=300,
            max_connection_pool_size=50,
            connection_acquisition_timeout=30,
        )
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


# ── Vector search ─────────────────────────────────────────────────────────────
# Single Cypher call: vector search + state/category filters.

VECTOR_SEARCH_CYPHER = """
CALL db.index.vector.queryNodes('scheme_embeddings', $top_k, $query_vector)
YIELD node AS s, score
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
WITH s, score,
     collect({field: r.field, operator: r.operator, value: r.value}) AS rules
RETURN s.id          AS scheme_id,
       s.name        AS scheme_name,
       s.summary     AS summary,
       s.source_url  AS source_url,
       s.last_verified AS last_verified,
       score,
       rules
ORDER BY score DESC
"""



def vector_search(
    query_vector: list[float],
    state: str | None,
    category: str | None,
    top_k: int = 20,
) -> list[dict]:
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                VECTOR_SEARCH_CYPHER,
                query_vector=query_vector,
                state=state,
                category=category,
                top_k=top_k,
            )
            return [dict(r) for r in result]
    except Exception as e:
        # Retry once with refreshed connection if session expired
        close_driver()
        driver = get_driver()
        with driver.session() as session:
            result = session.run(
                VECTOR_SEARCH_CYPHER,
                query_vector=query_vector,
                state=state,
                category=category,
                top_k=top_k,
            )
            return [dict(r) for r in result]


# ── Similar schemes (shared-neighbor) ─────────────────────────────────────────

SIMILAR_SCHEMES_CYPHER = """
MATCH (s1:Scheme {id: $scheme_id})-[:FOR_CATEGORY|APPLICABLE_IN|HAS_RULE]->(shared)
      <-[:FOR_CATEGORY|APPLICABLE_IN|HAS_RULE]-(s2:Scheme)
WHERE s1 <> s2
WITH s2, count(shared) AS overlap, collect(labels(shared)[0]) AS shared_labels
ORDER BY overlap DESC
LIMIT 5
RETURN s2.id          AS scheme_id,
       s2.name        AS scheme_name,
       s2.summary     AS summary,
       s2.source_url  AS source_url,
       overlap,
       shared_labels
"""


def get_similar_schemes(scheme_id: str) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(SIMILAR_SCHEMES_CYPHER, scheme_id=scheme_id)
        return [dict(r) for r in result]


# ── Fetch single scheme ────────────────────────────────────────────────────────

FETCH_SCHEME_CYPHER = """
MATCH (s:Scheme {id: $scheme_id})
RETURN s.id AS scheme_id, s.name AS scheme_name
"""


def scheme_exists(scheme_id: str) -> bool:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(FETCH_SCHEME_CYPHER, scheme_id=scheme_id)
        return result.single() is not None


# ── Recommend based on viewing history (multiple viewed schemes) ─────────────

HISTORY_RECOMMENDATIONS_CYPHER = """
MATCH (viewed:Scheme) WHERE viewed.id IN $viewed_ids
MATCH (viewed)-[:FOR_CATEGORY]->(cat)<-[:FOR_CATEGORY]-(rec:Scheme)
WHERE NOT rec.id IN $viewed_ids
WITH rec, count(DISTINCT cat) AS cat_score, collect(DISTINCT viewed.name)[..3] AS matched_names
RETURN rec.id         AS scheme_id,
       rec.name       AS scheme_name,
       rec.summary    AS summary,
       rec.source_url AS source_url,
       cat_score      AS overlap_score,
       matched_names  AS matched_viewed_names
ORDER BY overlap_score DESC
LIMIT $limit
"""


def get_recommendations_from_history(viewed_ids: list[str], limit: int = 5) -> list[dict]:
    """
    Given a list of viewed scheme IDs, traverse the Neo4j graph to find
    related schemes ranked by shared category connections.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(HISTORY_RECOMMENDATIONS_CYPHER, viewed_ids=viewed_ids, limit=limit)
        items = []
        for r in result:
            viewed_str = ", ".join(r["matched_viewed_names"]) if r["matched_viewed_names"] else "your history"
            items.append({
                "scheme_id": r["scheme_id"],
                "scheme_name": r["scheme_name"],
                "summary": r["summary"] or "",
                "source_url": r["source_url"],
                "overlap_score": r["overlap_score"],
                "reason": f"Recommended because you viewed '{viewed_str}' — they share similar target categories.",
            })
        return items


