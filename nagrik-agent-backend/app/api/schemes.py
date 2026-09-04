"""
app/api/schemes.py
------------------
REST endpoints for the Government Services catalog and recommendations.

Endpoints:
  GET  /api/schemes                   — list / search schemes from Neo4j
  GET  /api/schemes/{scheme_id}       — get a single scheme's full details
  GET  /api/schemes/recommendations   — personalized recommendations
  POST /api/schemes/track-view        — record a citizen viewing a scheme
"""
from __future__ import annotations

import os
import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.rag.neo4j_search import get_driver

router = APIRouter(prefix="/api/schemes")


# ---------------------------------------------------------------------------
# Helpers – map Neo4j Scheme node to the frontend Scheme shape
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    "agriculture": "Agriculture",
    "education": "Education",
    "health": "Health",
    "housing": "Housing",
    "employment": "Employment",
    "social welfare": "Social Welfare",
    "social": "Social Welfare",
    "women": "Women & Child",
    "child": "Women & Child",
    "pension": "Pension",
    "business": "Business & MSME",
    "msme": "Business & MSME",
    "energy": "Energy",
    "finance": "Business & MSME",
}

BENEFIT_TYPE_MAP: dict[str, str] = {
    "cash transfer": "Cash Transfer",
    "subsidy": "Subsidy",
    "insurance": "Insurance",
    "loan": "Loan",
    "service": "Service",
    "pension": "Pension",
    "scholarship": "Scholarship",
}

IMAGE_COLORS: dict[str, str] = {
    "Agriculture": "bg-green-50",
    "Education": "bg-amber-50",
    "Health": "bg-red-50",
    "Housing": "bg-blue-50",
    "Employment": "bg-violet-50",
    "Social Welfare": "bg-orange-50",
    "Women & Child": "bg-pink-50",
    "Pension": "bg-slate-50",
    "Business & MSME": "bg-indigo-50",
    "Energy": "bg-yellow-50",
}


def _norm_category(raw: str | None) -> str:
    if not raw:
        return "Social Welfare"
    lower = raw.lower().strip()
    for key, val in CATEGORY_MAP.items():
        if key in lower:
            return val
    return "Social Welfare"


def _norm_benefit_type(raw: str | None) -> str:
    if not raw:
        return "Service"
    lower = raw.lower().strip()
    for key, val in BENEFIT_TYPE_MAP.items():
        if key in lower:
            return val
    return "Service"


def _neo4j_row_to_scheme(row: dict) -> dict:
    """Convert a Neo4j Cypher result row to the frontend-compatible Scheme shape."""
    sid = row.get("scheme_id") or row.get("id") or ""
    name = row.get("scheme_name") or row.get("name") or "Unnamed Scheme"
    summary = row.get("summary") or ""
    source_url = row.get("source_url") or ""
    ministry = row.get("ministry") or ""
    department = row.get("department") or ""
    category_raw = row.get("category") or row.get("scheme_category") or ""
    level_raw = (row.get("level") or "Central").strip()
    level = "State" if level_raw.lower() == "state" else "Central"
    category = _norm_category(category_raw)
    benefit_type = _norm_benefit_type(row.get("benefit_type") or "")
    # Deduplicate and clean tags
    tags_raw = row.get("tags") or []
    if isinstance(tags_raw, str):
        tags_raw = [t.strip() for t in tags_raw.split(",") if t.strip()]
    tags = list(dict.fromkeys(tags_raw))[:6]

    rules_raw = row.get("rules") or []
    # Normalise rule dicts – Neo4j may return None-valued fields
    eligibility_rules = []
    for r in rules_raw:
        if not isinstance(r, dict):
            continue
        field = r.get("field") or ""
        if not field:
            continue
        eligibility_rules.append({
            "field": field,
            "label": r.get("label") or field.replace("_", " ").title(),
            "operator": r.get("operator") or "eq",
            "value": r.get("value") or "",
        })

    docs = row.get("documents") or []
    states = row.get("states") or []
    categories_list = row.get("categories") or []

    eligibility_summary = row.get("eligibility_summary") or categories_list[:4] or [
        "Check official portal for eligibility criteria."
    ]
    if isinstance(eligibility_summary, str):
        eligibility_summary = [eligibility_summary]

    return {
        "id": sid,
        "title": name,
        "shortDescription": summary[:160] if summary else f"{name} – government scheme.",
        "description": summary or f"{name} is a government scheme offered by {ministry or department}.",
        "category": category,
        "level": level,
        "department": department or ministry,
        "ministry": ministry or department,
        "benefitAmount": row.get("benefit_amount") or None,
        "benefitType": benefit_type,
        "tags": tags if tags else [category.lower()],
        "eligibilityRules": eligibility_rules,
        "eligibilitySummary": eligibility_summary,
        "documentsRequired": docs[:8] if docs else ["Aadhaar Card", "Bank Account Details"],
        "applicationSteps": [
            "Visit the official portal or CSC centre.",
            "Fill in the application form with required details.",
            "Upload supporting documents.",
            "Submit and track application status.",
        ],
        "officialSourceUrl": source_url or "https://india.gov.in",
        "officialSourceName": (source_url.replace("https://", "").replace("http://", "").split("/")[0]
                               if source_url else "india.gov.in"),
        "lastVerified": datetime.utcnow().strftime("%Y-%m-%d"),
        "launchedOn": row.get("launched_on") or "2015-01-01",
        "beneficiariesCount": int(row.get("beneficiaries_count") or 0),
        "rating": float(row.get("rating") or 4.0),
        "processingTimeDays": int(row.get("processing_time_days") or 30),
        "isFeatured": bool(row.get("is_featured") or False),
        "imageColor": IMAGE_COLORS.get(category, "bg-slate-50"),
    }


# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

LIST_SCHEMES_CYPHER = """
MATCH (s:Scheme)
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
OPTIONAL MATCH (s)-[:REQUIRES]->(d:Document)
OPTIONAL MATCH (s)-[:APPLICABLE_IN]->(st:State)
OPTIONAL MATCH (s)-[:FOR_CATEGORY]->(cat:BeneficiaryCategory)
OPTIONAL MATCH (s)<-[:OFFERS]-(dept:Department)<-[:HAS_DEPARTMENT]-(min:Ministry)
WITH s,
     collect(DISTINCT {field: r.field, operator: r.operator, value: r.value, label: r.label}) AS rules,
     collect(DISTINCT d.type) AS documents,
     collect(DISTINCT st.name) AS states,
     collect(DISTINCT cat.name) AS categories,
     head(collect(DISTINCT dept.name)) AS department,
     head(collect(DISTINCT min.name)) AS ministry
WHERE ($search_query = '' OR toLower(s.name) CONTAINS toLower($search_query) OR toLower(s.summary) CONTAINS toLower($search_query))
  AND ($search_level = 'All' OR toLower(s.level) = toLower($search_level))
RETURN
  s.id AS scheme_id,
  s.name AS scheme_name,
  s.summary AS summary,
  s.source_url AS source_url,
  s.level AS level,
  s.benefit_type AS benefit_type,
  s.benefit_amount AS benefit_amount,
  s.beneficiaries_count AS beneficiaries_count,
  s.rating AS rating,
  s.launched_on AS launched_on,
  s.is_featured AS is_featured,
  s.tags AS tags,
  department,
  ministry,
  categories[0] AS scheme_category,
  rules,
  documents,
  states,
  categories
ORDER BY s.is_featured DESC, s.name ASC
SKIP $skip
LIMIT $limit
"""

GET_SCHEME_CYPHER = """
MATCH (s:Scheme {id: $scheme_id})
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
OPTIONAL MATCH (s)-[:REQUIRES]->(d:Document)
OPTIONAL MATCH (s)-[:APPLICABLE_IN]->(st:State)
OPTIONAL MATCH (s)-[:FOR_CATEGORY]->(cat:BeneficiaryCategory)
OPTIONAL MATCH (s)<-[:OFFERS]-(dept:Department)<-[:HAS_DEPARTMENT]-(min:Ministry)
WITH s,
     collect(DISTINCT {field: r.field, operator: r.operator, value: r.value, label: r.label}) AS rules,
     collect(DISTINCT d.type) AS documents,
     collect(DISTINCT st.name) AS states,
     collect(DISTINCT cat.name) AS categories,
     head(collect(DISTINCT dept.name)) AS department,
     head(collect(DISTINCT min.name)) AS ministry
RETURN
  s.id AS scheme_id,
  s.name AS scheme_name,
  s.summary AS summary,
  s.source_url AS source_url,
  s.level AS level,
  s.benefit_type AS benefit_type,
  s.benefit_amount AS benefit_amount,
  s.beneficiaries_count AS beneficiaries_count,
  s.rating AS rating,
  s.launched_on AS launched_on,
  s.is_featured AS is_featured,
  s.tags AS tags,
  department,
  ministry,
  categories[0] AS scheme_category,
  rules,
  documents,
  states,
  categories
"""

TRACK_VIEW_CYPHER = """
MERGE (c:Citizen {id: $citizen_id})
WITH c
MATCH (s:Scheme {id: $scheme_id})
MERGE (c)-[v:VIEWED]->(s)
ON CREATE SET v.first_viewed = $ts, v.count = 1
ON MATCH  SET v.last_viewed = $ts, v.count = coalesce(v.count, 0) + 1
RETURN s.id AS scheme_id, v.count AS view_count
"""

RECOMMENDATIONS_CYPHER = """
// Step 1: Profile-based scoring — schemes whose category nodes match citizen's viewed categories
MATCH (s:Scheme)
OPTIONAL MATCH (s)-[:HAS_RULE]->(r:EligibilityRule)
OPTIONAL MATCH (s)-[:FOR_CATEGORY]->(cat:BeneficiaryCategory)
OPTIONAL MATCH (s)-[:APPLICABLE_IN]->(st:State)
OPTIONAL MATCH (s)<-[:OFFERS]-(dept:Department)<-[:HAS_DEPARTMENT]-(min:Ministry)
OPTIONAL MATCH (s)-[:REQUIRES]->(d:Document)
WITH s,
     collect(DISTINCT {field: r.field, operator: r.operator, value: r.value, label: r.label}) AS rules,
     collect(DISTINCT cat.name) AS categories,
     collect(DISTINCT st.name) AS states,
     collect(DISTINCT d.type) AS documents,
     head(collect(DISTINCT dept.name)) AS department,
     head(collect(DISTINCT min.name)) AS ministry

// Step 2: Check if citizen has viewed this scheme (or similar)
OPTIONAL MATCH (c:Citizen {id: $citizen_id})-[v:VIEWED]->(s)
// Step 3: Count co-viewed — other citizens who viewed this scheme also viewed what?
OPTIONAL MATCH (c2:Citizen)-[:VIEWED]->(s) WHERE c2.id <> $citizen_id
WITH s, rules, categories, states, documents, department, ministry,
     coalesce(v.count, 0) AS personal_views,
     count(DISTINCT c2) AS social_views

// Calculate a base relevance score from social signal + personal history
WITH s, rules, categories, states, documents, department, ministry,
     personal_views,
     (personal_views * 2 + social_views) AS graph_score

RETURN
  s.id AS scheme_id,
  s.name AS scheme_name,
  s.summary AS summary,
  s.source_url AS source_url,
  s.level AS level,
  s.benefit_type AS benefit_type,
  s.benefit_amount AS benefit_amount,
  s.beneficiaries_count AS beneficiaries_count,
  s.rating AS rating,
  s.launched_on AS launched_on,
  s.is_featured AS is_featured,
  s.tags AS tags,
  department,
  ministry,
  categories[0] AS scheme_category,
  rules,
  documents,
  states,
  categories,
  graph_score,
  personal_views
ORDER BY graph_score DESC, s.is_featured DESC
LIMIT $limit
"""


# ---------------------------------------------------------------------------
# Eligibility scoring (profile-side, runs in Python after fetching schemes)
# ---------------------------------------------------------------------------

def _compute_profile_match(scheme_dict: dict, profile: dict) -> int:
    """Return 0-100 match score comparing citizen profile against scheme rules."""
    rules = scheme_dict.get("eligibilityRules") or []
    if not rules:
        return 70  # default when no rules defined

    met = 0
    for rule in rules:
        field = rule.get("field", "")
        op = rule.get("operator", "eq")
        val = rule.get("value")
        try:
            if field == "income":
                citizen_income = profile.get("income") or 0
                if op == "lte":
                    met += 1 if citizen_income <= float(val) else 0
                elif op == "gte":
                    met += 1 if citizen_income >= float(val) else 0
                else:
                    met += 1
            elif field == "gender":
                met += 1 if (profile.get("gender") or "").lower() == str(val).lower() else 0
            elif field == "category":
                cats = val if isinstance(val, list) else [val]
                met += 1 if (profile.get("category") or "") in cats else 0
            elif field == "age":
                dob = profile.get("dob") or "1990-01-01"
                try:
                    age = (datetime.utcnow().date() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
                except Exception:
                    age = 30
                if op == "between" and isinstance(val, list) and len(val) == 2:
                    met += 1 if val[0] <= age <= val[1] else 0
                elif op == "lte":
                    met += 1 if age <= float(val) else 0
                elif op == "gte":
                    met += 1 if age >= float(val) else 0
                else:
                    met += 1
            else:
                # Unknown/unverifiable rule — give benefit of the doubt
                met += 1
        except Exception:
            met += 1  # don't penalise for data errors

    return math.floor((met / len(rules)) * 100)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TrackViewRequest(BaseModel):
    citizen_id: str
    scheme_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def list_schemes(
    query: str = Query(default="", description="Text search on name/summary"),
    category: str = Query(default="All", description="Scheme category filter"),
    level: str = Query(default="All", description="Central | State | All"),
    sort: str = Query(default="relevance", description="relevance|newest|beneficiaries|rating"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List government schemes from Neo4j with optional filters."""
    global _driver
    from app.rag.neo4j_search import get_driver, _driver as nd
    driver = get_driver()

    try:
        with driver.session() as sess:
            result = sess.run(
                LIST_SCHEMES_CYPHER,
                search_query=query or "",
                search_level=level if level != "All" else "All",
                skip=offset,
                limit=limit,
            )
            rows = [dict(r) for r in result]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j query failed: {e}")

    schemes = [_neo4j_row_to_scheme(r) for r in rows]

    # Category filter (post-query since Neo4j categories are nodes not a property)
    if category and category != "All":
        schemes = [s for s in schemes if s["category"] == category]

    # Sort
    if sort == "newest":
        schemes.sort(key=lambda s: s.get("launchedOn") or "", reverse=True)
    elif sort == "beneficiaries":
        schemes.sort(key=lambda s: s.get("beneficiariesCount") or 0, reverse=True)
    elif sort == "rating":
        schemes.sort(key=lambda s: s.get("rating") or 0, reverse=True)
    else:
        # Relevance: featured first
        schemes.sort(key=lambda s: (0 if s.get("isFeatured") else 1, s["title"]))

    return {"schemes": schemes, "total": len(schemes), "offset": offset, "limit": limit}


@router.get("/recommendations")
async def get_recommendations(
    citizen_id: str = Query(default="cz-10234"),
    income: Optional[int] = Query(default=None),
    age: Optional[int] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    dob: Optional[str] = Query(default=None),
    limit: int = Query(default=6, ge=1, le=20),
):
    """
    Return personalised scheme recommendations based on:
    1. Citizen's VIEWED history in the knowledge graph
    2. Profile-based eligibility rule matching
    """
    from app.rag.neo4j_search import get_driver
    driver = get_driver()

    profile = {
        "income": income,
        "gender": gender,
        "category": category,
        "dob": dob,
    }

    try:
        with driver.session() as sess:
            result = sess.run(
                RECOMMENDATIONS_CYPHER,
                citizen_id=citizen_id,
                limit=limit * 4,  # fetch more, then re-rank
            )
            rows = [dict(r) for r in result]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j recommendations query failed: {e}")

    schemes = []
    for row in rows:
        s = _neo4j_row_to_scheme(row)
        graph_score = int(row.get("graph_score") or 0)
        personal_views = int(row.get("personal_views") or 0)
        profile_score = _compute_profile_match(s, profile)
        # Blend: 60% profile eligibility + 30% graph/social + 10% personal views bonus
        bonus = min(personal_views * 5, 20)  # up to +20 for heavily viewed
        blended = int(profile_score * 0.6 + min(graph_score * 3, 30) + bonus)
        blended = min(blended, 100)
        s["_matchScore"] = blended
        s["_graphScore"] = graph_score
        schemes.append(s)

    # Sort by blended score, then featured
    schemes.sort(key=lambda s: (-(s["_matchScore"]), 0 if s.get("isFeatured") else 1))

    # Deduplicate by id
    seen = set()
    deduped = []
    for s in schemes:
        if s["id"] not in seen:
            seen.add(s["id"])
            deduped.append(s)

    top = deduped[:limit]

    clean = []
    for s in top:
        ms = s.pop("_matchScore", 60)
        gs = s.pop("_graphScore", 0)
        s["matchScore"] = ms
        s["graphScore"] = gs
        clean.append(s)

    return {"recommendations": clean}



@router.get("/{scheme_id}")
async def get_scheme(scheme_id: str):
    """Get full details for a single scheme."""
    from app.rag.neo4j_search import get_driver
    driver = get_driver()

    try:
        with driver.session() as sess:
            result = sess.run(GET_SCHEME_CYPHER, scheme_id=scheme_id)
            row = result.single()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j query failed: {e}")

    if not row:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found in Neo4j")

    return _neo4j_row_to_scheme(dict(row))


@router.post("/track-view")
async def track_view(body: TrackViewRequest):
    """
    Record that a citizen viewed a scheme.
    Creates/updates a (:Citizen)-[:VIEWED]->(:Scheme) relationship in Neo4j.
    This feeds the view-history cache used for recommendations.
    """
    from app.rag.neo4j_search import get_driver
    driver = get_driver()

    ts = datetime.utcnow().isoformat()
    try:
        with driver.session() as sess:
            result = sess.run(
                TRACK_VIEW_CYPHER,
                citizen_id=body.citizen_id,
                scheme_id=body.scheme_id,
                ts=ts,
            )
            row = result.single()
    except Exception as e:
        # Non-fatal — don't break the UI if tracking fails
        return {"tracked": False, "error": str(e)}

    if not row:
        return {"tracked": False, "error": "Scheme not found in graph"}

    return {"tracked": True, "scheme_id": row["scheme_id"], "view_count": row["view_count"]}
