"""
api/main.py
-----------
FastAPI application with:

  POST /schemes/search          - Eligibility-aware scheme search
  GET  /schemes/{id}/similar    - Graph-based similar schemes
  POST /schemes/recommend-history - History-based recommendations

  POST /user/profile            - Create/update citizen profile (auth required)
  GET  /user/profile            - Get current user's profile (auth required)
  POST /user/history/view       - Record a scheme view (auth required)
  GET  /user/history            - Get user's view history (auth required)
  GET  /user/recommendations    - Get personalised recommendations from history (auth required)
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sentence_transformers import SentenceTransformer

from api.auth import get_current_user_id
from api.eligibility import evaluate_eligibility
from api.graph import (
    close_driver,
    get_driver,
    get_recommendations_from_history,
    get_similar_schemes,
    scheme_exists,
    vector_search,
)
from api.models import (
    CitizenProfile,
    HistoryRecommendationRequest,
    SchemeResult,
    SchemeViewRequest,
    SearchResponse,
    SimilarResponse,
    SimilarScheme,
    UserProfileUpsert,
)
from api.supabase_client import get_supabase

# ── Embedding model (loaded once at startup) ──────────────────────────────────
_embed_model: SentenceTransformer | None = None
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _embed_model
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("[startup] Loading embedding model ...")
    _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    # Warm up Neo4j connection
    try:
        get_driver().verify_connectivity()
        print("[startup] Neo4j connected OK")
    except Exception as e:
        print(f"[startup] WARNING: Neo4j connection failed: {e}")
    yield
    close_driver()
    print("[shutdown] Driver closed.")


app = FastAPI(
    title="Government Schemes Knowledge Graph API",
    description=(
        "Retrieval + recommendation API backed by a Neo4j knowledge graph "
        "of Indian government welfare schemes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def get_embedding(text: str) -> list[float]:
    assert _embed_model is not None, "Embedding model not loaded"
    emb = _embed_model.encode(text, normalize_embeddings=True)
    return emb.tolist()


# ── Plain-language reason builder ─────────────────────────────────────────────
LABEL_TO_PHRASE = {
    "BeneficiaryCategory": "for {name}",
    "State": "available in {name}",
    "EligibilityRule": "shares eligibility criteria",
}

def build_reason(shared_labels: list[str], scheme_name: str) -> str:
    """Turn a list of node labels into a human-readable similarity reason."""
    phrases = []
    label_counts: dict[str, int] = {}
    for lbl in shared_labels:
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    for lbl, count in label_counts.items():
        if lbl == "BeneficiaryCategory":
            phrases.append(f"targets similar beneficiary groups")
        elif lbl == "State":
            phrases.append(f"applicable in the same state(s)")
        elif lbl == "EligibilityRule":
            phrases.append(f"shares {count} eligibility criterion/criteria")

    if not phrases:
        return f"Similar to {scheme_name}"
    return "Also " + "; ".join(phrases)


# ── POST /schemes/search ──────────────────────────────────────────────────────

@app.post("/schemes/search", response_model=SearchResponse, tags=["Search"])
async def search_schemes(profile: CitizenProfile):
    """
    Given a citizen profile + free-text need description, returns ranked
    government schemes with deterministic eligibility evaluation.

    - Embeds the query and performs Neo4j vector search filtered by state/category.
    - Evaluates EligibilityRule nodes in Python (no LLM) for each candidate.
    - Returns Eligible / Not Eligible / Uncertain with rule-level details.
    """
    if not profile.query.strip():
        raise HTTPException(status_code=400, detail="`query` must not be empty.")

    # 1. Embed free-text query
    query_vector = get_embedding(profile.query)

    # 2. Vector search + graph filter
    raw_results = vector_search(
        query_vector=query_vector,
        state=profile.state,
        category=profile.category,
        top_k=30,  # over-fetch; we'll re-rank after eligibility check
    )

    # 3. Evaluate eligibility deterministically
    output: list[SchemeResult] = []
    for row in raw_results:
        rules: list[dict] = row.get("rules") or []
        # Filter out null rules (OPTIONAL MATCH artifacts)
        rules = [r for r in rules if r.get("field")]

        status, evaluations = evaluate_eligibility(rules, profile)

        output.append(
            SchemeResult(
                scheme_id=row["scheme_id"],
                scheme_name=row["scheme_name"],
                summary=row["summary"] or "",
                source_url=row.get("source_url"),
                last_verified=row.get("last_verified"),
                eligibility_status=status,
                rule_evaluations=evaluations,
                vector_score=round(float(row.get("score", 0.0)), 4),
            )
        )

    # 4. Sort: Eligible first, then Uncertain, then Not Eligible; within each
    #    group sort by vector score desc.
    STATUS_ORDER = {"Eligible": 0, "Uncertain": 1, "Not Eligible": 2}
    output.sort(key=lambda r: (STATUS_ORDER[r.eligibility_status], -(r.vector_score or 0)))

    return SearchResponse(
        query=profile.query,
        total_candidates=len(output),
        results=output,
    )


# ── GET /schemes/{id}/similar ─────────────────────────────────────────────────

@app.get("/schemes/{scheme_id}/similar", response_model=SimilarResponse, tags=["Recommendations"])
async def similar_schemes(scheme_id: str):
    """
    Returns up to 5 similar schemes for a given scheme ID using shared-neighbor
    Cypher traversal across category, state, and eligibility-rule nodes.
    """
    if not scheme_exists(scheme_id):
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found.")

    raw = get_similar_schemes(scheme_id)

    similar: list[SimilarScheme] = []
    for row in raw:
        shared_labels: list[str] = row.get("shared_labels") or []
        reason = build_reason(shared_labels, row["scheme_name"])
        similar.append(
            SimilarScheme(
                scheme_id=row["scheme_id"],
                scheme_name=row["scheme_name"],
                summary=row["summary"] or "",
                source_url=row.get("source_url"),
                overlap_count=row["overlap"],
                shared_via=shared_labels,
                reason=reason,
            )
        )

    return SimilarResponse(scheme_id=scheme_id, similar_schemes=similar)


# ── POST /schemes/recommend-history ──────────────────────────────────────────

@app.post("/schemes/recommend-history", tags=["Recommendations"])
async def recommend_from_history(req: HistoryRecommendationRequest):
    """
    Given a list of previously viewed scheme IDs, returns ranked scheme
    recommendations via Neo4j graph traversal (no auth required — can be
    used with anonymous session history too).
    """
    if not req.viewed_scheme_ids:
        raise HTTPException(status_code=400, detail="`viewed_scheme_ids` must not be empty.")
    recs = get_recommendations_from_history(req.viewed_scheme_ids, limit=req.limit)
    return {
        "viewed_schemes": req.viewed_scheme_ids,
        "recommendations_count": len(recs),
        "recommendations": recs,
    }


# ── POST /user/profile ────────────────────────────────────────────────────────

@app.post("/user/profile", tags=["User"])
async def upsert_profile(
    profile: UserProfileUpsert,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create or update the authenticated citizen's profile.
    Send Authorization: Bearer <supabase_access_token>
    """
    sb = get_supabase()
    data = {"id": user_id, **profile.model_dump(exclude_none=True)}
    sb.table("user_profiles").upsert(data, on_conflict="id").execute()
    return {"status": "ok", "profile": data}


# ── GET /user/profile ─────────────────────────────────────────────────────────

@app.get("/user/profile", tags=["User"])
async def get_profile(user_id: str = Depends(get_current_user_id)):
    """
    Fetch the authenticated user's saved profile.
    """
    sb = get_supabase()
    res = sb.table("user_profiles").select("*").eq("id", user_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found. Create one via POST /user/profile")
    return res.data


# ── POST /user/history/view ───────────────────────────────────────────────────

@app.post("/user/history/view", tags=["User"])
async def record_view(
    req: SchemeViewRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Record that the authenticated user viewed a scheme.
    Call this whenever a user opens a scheme's detail page.
    """
    sb = get_supabase()
    sb.table("scheme_view_history").insert({
        "user_id": user_id,
        "scheme_id": req.scheme_id,
        "scheme_name": req.scheme_name,
    }).execute()
    return {"status": "recorded", "scheme_id": req.scheme_id}


# ── GET /user/history ─────────────────────────────────────────────────────────

@app.get("/user/history", tags=["User"])
async def get_history(
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
):
    """
    Return the authenticated user's most recently viewed schemes.
    """
    sb = get_supabase()
    res = (
        sb.table("scheme_view_history")
        .select("scheme_id, scheme_name, viewed_at")
        .eq("user_id", user_id)
        .order("viewed_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"user_id": user_id, "history": res.data or []}


# ── GET /user/recommendations ─────────────────────────────────────────────────

@app.get("/user/recommendations", tags=["User"])
async def get_user_recommendations(
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
):
    """
    Personalised scheme recommendations based on the user's view history.
    1. Reads last 30 viewed scheme IDs from Supabase.
    2. Passes them to the Neo4j graph traversal engine.
    3. Returns ranked recommendations with plain-language reasons.
    """
    sb = get_supabase()
    res = (
        sb.table("scheme_view_history")
        .select("scheme_id")
        .eq("user_id", user_id)
        .order("viewed_at", desc=True)
        .limit(30)
        .execute()
    )
    viewed_ids = list({r["scheme_id"] for r in (res.data or [])})
    if not viewed_ids:
        return {
            "user_id": user_id,
            "message": "No viewing history yet. View some schemes first!",
            "recommendations": [],
        }
    recs = get_recommendations_from_history(viewed_ids, limit=limit)
    return {
        "user_id": user_id,
        "based_on_viewed": viewed_ids,
        "recommendations_count": len(recs),
        "recommendations": recs,
    }


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "model": EMBED_MODEL_NAME}


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
