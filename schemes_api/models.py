"""
api/models.py
-------------
Pydantic request/response models for the FastAPI endpoints.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ── Shared types ──────────────────────────────────────────────────────────────

class CitizenProfile(BaseModel):
    state: str | None = Field(None, description="Applicant's state of residence")
    occupation: str | None = Field(None, description="e.g. farmer, student, labourer")
    income_annual: float | None = Field(None, description="Annual household income in INR")
    category: str | None = Field(None, description="e.g. SC, ST, OBC, General")
    age: int | None = Field(None, description="Age in years")
    gender: str | None = Field(None, description="male / female / other")
    disability: bool | None = Field(None, description="Whether the applicant has a disability")
    marital_status: str | None = Field(None, description="single / married / widowed / divorced")
    religion: str | None = Field(None, description="e.g. Hindu, Muslim, Christian")
    query: str = Field(..., description="Free-text description of what the applicant needs")


# ── /schemes/search ───────────────────────────────────────────────────────────

class RuleEvaluation(BaseModel):
    field: str
    operator: str
    value: str
    status: Literal["passed", "failed", "uncertain"]
    reason: str | None = None


class SchemeResult(BaseModel):
    scheme_id: str
    scheme_name: str
    summary: str
    source_url: str | None
    last_verified: str | None
    eligibility_status: Literal["Eligible", "Not Eligible", "Uncertain"]
    rule_evaluations: list[RuleEvaluation]
    vector_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    total_candidates: int
    results: list[SchemeResult]


# ── /schemes/{id}/similar ─────────────────────────────────────────────────────

class SimilarScheme(BaseModel):
    scheme_id: str
    scheme_name: str
    summary: str
    source_url: str | None
    overlap_count: int
    shared_via: list[str]
    reason: str


class SimilarResponse(BaseModel):
    scheme_id: str
    similar_schemes: list[SimilarScheme]


# ── /user/profile ─────────────────────────────────────────────────────────────

class UserProfileUpsert(BaseModel):
    name: str | None = Field(None, description="Full name")
    age: int | None = Field(None, ge=1, le=120, description="Age in years")
    state: str | None = Field(None, description="State of residence, e.g. Rajasthan")
    category: str | None = Field(None, description="SC / ST / OBC / General / EWS")
    occupation: str | None = Field(None, description="e.g. farmer, student, labourer, salaried")
    income_annual: int | None = Field(None, ge=0, description="Annual household income in INR")
    gender: str | None = Field(None, description="male / female / other")
    disability: bool | None = Field(None, description="Whether the user has a disability")
    marital_status: str | None = Field(None, description="single / married / widowed / divorced")


# ── /user/history ─────────────────────────────────────────────────────────────

class SchemeViewRequest(BaseModel):
    scheme_id: str = Field(..., description="Scheme slug/ID, e.g. 'aif'")
    scheme_name: str = Field(..., description="Human-readable scheme name")


# ── /schemes/recommend-history ────────────────────────────────────────────────

class HistoryRecommendationRequest(BaseModel):
    viewed_scheme_ids: list[str] = Field(
        ..., description="List of scheme IDs viewed in the past", example=["aif", "avgsy"]
    )
    limit: int = Field(5, ge=1, le=20, description="Number of recommendations to return")

