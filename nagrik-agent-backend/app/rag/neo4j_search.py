"""
app/rag/neo4j_search.py
-----------------------
Neo4j-backed knowledge graph search — replaces ChromaDB entirely.

Provides:
  - vector_search()         : semantic similarity via Neo4j vector index
  - graph_context_search()  : graph traversal for scheme context
  - hybrid_search()         : vector + graph combined (main entry point)
"""
import os
from functools import lru_cache
from typing import Optional
from neo4j import GraphDatabase, Driver
from sentence_transformers import SentenceTransformer

NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j+s://50580f6d.databases.neo4j.io")
NEO4J_USER     = os.getenv("NEO4J_USER", "50580f6d")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "PUR0KsbQ26WeiRG5ta1557FSE16XwGRdolaFK3-2jBI")

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_driver: Optional[Driver] = None
_model: Optional[SentenceTransformer] = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=10,
            max_connection_lifetime=180,
            liveness_check_timeout=1.0,
            connection_acquisition_timeout=15.0,
        )
    return _driver


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL_NAME)


# ── Vector search ─────────────────────────────────────────────────────────────
VECTOR_SEARCH_CYPHER = """
CALL db.index.vector.queryNodes('scheme_embeddings', $top_k, $query_vector)
YIELD node AS s, score
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
OPTIONAL MATCH (s)<-[:OFFERS]-(dept:Department)<-[:HAS_DEPARTMENT]-(min:Ministry)
WITH s, score,
     collect({field: r.field, operator: r.operator, value: r.value}) AS rules,
     head(collect(dept.name)) AS department,
     head(collect(min.name)) AS ministry
RETURN s.id          AS scheme_id,
       s.name        AS scheme_name,
       s.summary     AS summary,
       s.source_url  AS source_url,
       department,
       ministry,
       score,
       rules
ORDER BY score DESC
"""

GRAPH_CONTEXT_CYPHER = """
MATCH (s:Scheme {id: $scheme_id})
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
OPTIONAL MATCH (s)-[:REQUIRES]->(d:Document)
OPTIONAL MATCH (s)-[:APPLICABLE_IN]->(st:State)
OPTIONAL MATCH (s)-[:FOR_CATEGORY]->(cat:BeneficiaryCategory)
OPTIONAL MATCH (s)<-[:OFFERS]-(dept:Department)<-[:HAS_DEPARTMENT]-(min:Ministry)
RETURN
  s.name AS scheme_name,
  s.summary AS summary,
  s.source_url AS source_url,
  head(collect(DISTINCT min.name)) AS ministry,
  head(collect(DISTINCT dept.name)) AS department,
  collect(DISTINCT {field: r.field, operator: r.operator, value: r.value}) AS rules,
  collect(DISTINCT d.type) AS documents,
  collect(DISTINCT st.name) AS states,
  collect(DISTINCT cat.name) AS categories
"""


def vector_search(query: str, top_k: int = 8) -> list[dict]:
    """Semantic vector search over Neo4j scheme embeddings with retry on reconnect."""
    global _driver
    model = get_model()
    query_vector = model.encode(query, normalize_embeddings=True).tolist()
    for attempt in range(2):
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run(VECTOR_SEARCH_CYPHER, query_vector=query_vector, top_k=top_k)
                return [dict(r) for r in result]
        except Exception as e:
            print(f"[neo4j_search] vector_search attempt {attempt+1} error: {e}")
            try:
                if _driver:
                    _driver.close()
            except Exception:
                pass
            _driver = None
    return []


def graph_context(scheme_id: str) -> dict:
    """Fetch full graph context for a specific scheme with retry on reconnect."""
    global _driver
    for attempt in range(2):
        driver = get_driver()
        try:
            with driver.session() as session:
                result = session.run(GRAPH_CONTEXT_CYPHER, scheme_id=scheme_id)
                row = result.single()
                return dict(row) if row else {}
        except Exception as e:
            print(f"[neo4j_search] graph_context attempt {attempt+1} error: {e}")
            try:
                if _driver:
                    _driver.close()
            except Exception:
                pass
            _driver = None
    return {}


def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Main entry point: vector search to find top-k schemes,
    then enrich each with full graph context (rules, docs, states, categories).

    Returns list of dicts with keys:
      scheme_id, scheme_name, summary, source_url, ministry, department,
      score, rules, documents, states, categories
    """
    hits = vector_search(query, top_k=top_k * 2)
    if not hits:
        return []

    enriched = []
    seen = set()
    for hit in hits:
        sid = hit.get("scheme_id")
        if not sid or sid in seen:
            continue
        seen.add(sid)

        ctx = graph_context(sid)
        enriched.append({
            "scheme_id":   sid,
            "scheme_name": hit.get("scheme_name") or ctx.get("scheme_name", ""),
            "summary":     hit.get("summary") or ctx.get("summary", ""),
            "source_url":  hit.get("source_url") or ctx.get("source_url", ""),
            "ministry":    hit.get("ministry") or ctx.get("ministry", ""),
            "department":  hit.get("department") or ctx.get("department", ""),
            "score":       hit.get("score", 0),
            "rules":       ctx.get("rules") or hit.get("rules") or [],
            "documents":   ctx.get("documents") or [],
            "states":      ctx.get("states") or [],
            "categories":  ctx.get("categories") or [],
        })

        if len(enriched) >= top_k:
            break

    return enriched


def format_for_rag(results: list[dict]) -> str:
    """Format Neo4j search results into text chunks for the LLM."""
    if not results:
        return "No matching government schemes found."

    parts = []
    for i, r in enumerate(results, 1):
        lines = [f"[{i}] {r['scheme_name']}"]
        if r.get("ministry"):
            lines.append(f"Ministry: {r['ministry']}")
        if r.get("department"):
            lines.append(f"Department: {r['department']}")
        if r.get("summary"):
            lines.append(f"Summary: {r['summary']}")
        if r.get("categories"):
            lines.append(f"Beneficiaries: {', '.join(r['categories'])}")
        if r.get("states"):
            lines.append(f"Applicable in: {', '.join(r['states'][:5])}")
        if r.get("documents"):
            lines.append(f"Required docs: {', '.join(r['documents'][:6])}")
        if r.get("rules"):
            rule_texts = [
                f"{rule.get('field','')} {rule.get('operator','')} {rule.get('value','')}"
                for rule in r["rules"] if isinstance(rule, dict) and rule.get("field")
            ]
            if rule_texts:
                lines.append(f"Eligibility rules: {'; '.join(rule_texts[:5])}")
        if r.get("source_url"):
            lines.append(f"Source: {r['source_url']}")
        parts.append("\n".join(lines))

    return "\n\n---\n\n".join(parts)
