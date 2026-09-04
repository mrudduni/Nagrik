"""
Complaint REST endpoints for the citizen-facing UI.

POST /complaints/classify  – classify complaint text, return category/severity/dept
POST /complaints           – file a complaint, returns NGR-XXXXXX ID
GET  /complaints/{id}      – retrieve complaint status by ID

These wrap the same self-contained classifier used by the LangGraph tools so
all complaint logic lives in one place.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.graph.tools.complaint_tools import (
    _classify_by_keywords,
    _get_severity,
    _priority_tier,
    _generate_complaint_id,
    _human_category,
    _DEPARTMENT_MAP,
    _SLA_HOURS_MAP,
    _COMPLAINT_STORE,
)
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["complaints"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    description: str = Field(..., min_length=5)


class ClassifyResponse(BaseModel):
    category: str
    category_code: str
    confidence: float
    suggested_department: str
    suggested_severity: str
    severity_level: int


class FileComplaintRequest(BaseModel):
    citizen_id: str
    title: str
    description: str
    category: str           # human label or code, we normalise
    severity: str           # "low" | "medium" | "high" | "critical"
    department: str
    address: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: str
    reference_number: str
    category: str
    category_code: str
    priority: str
    department: str
    status: str
    sla_hours: int
    created_at: str
    address: Optional[str] = None


class ComplaintStatusResponse(BaseModel):
    id: str
    reference_number: str
    category: str
    priority: str
    department: str
    status: str
    sla_hours: int
    created_at: str
    address: Optional[str] = None
    found: bool = True


# ─── Severity mapping ─────────────────────────────────────────────────────────

_SEVERITY_LABEL_TO_INT = {
    "low": 2, "medium": 3, "high": 4, "critical": 5,
}
_SEVERITY_INT_TO_LABEL = {v: k for k, v in _SEVERITY_LABEL_TO_INT.items()}


def _tier_to_severity_label(tier: str) -> str:
    return {
        "CRITICAL": "critical",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }.get(tier, "medium")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/classify", response_model=ClassifyResponse)
async def classify_complaint(body: ClassifyRequest):
    """
    Classify a complaint description into category, severity, and department.
    Used by the "Report Issue" UI before filing.
    """
    text = body.description.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Description must not be empty.")

    category_code = _classify_by_keywords(text)
    severity_int = _get_severity(text, category_code)
    tier = _priority_tier(severity_int)
    department = _DEPARTMENT_MAP.get(category_code, _DEPARTMENT_MAP["OTHER"])
    severity_label = _tier_to_severity_label(tier)

    # Confidence heuristic: keyword match = 0.88, fallback OTHER = 0.55
    confidence = 0.55 if category_code == "OTHER" else 0.88

    return ClassifyResponse(
        category=_human_category(category_code),
        category_code=category_code,
        confidence=confidence,
        suggested_department=department,
        suggested_severity=severity_label,
        severity_level=severity_int,
    )


@router.post("", response_model=ComplaintResponse, status_code=201)
async def file_complaint(body: FileComplaintRequest):
    """
    File a complaint. Returns an NGR-XXXXXX reference ID.
    """
    if not body.description.strip():
        raise HTTPException(status_code=400, detail="Description must not be empty.")

    # Classify the description to get canonical category/priority
    category_code = _classify_by_keywords(body.description)
    severity_int = _get_severity(body.description, category_code)
    tier = _priority_tier(severity_int)
    department = _DEPARTMENT_MAP.get(category_code, _DEPARTMENT_MAP["OTHER"])
    sla = _SLA_HOURS_MAP[tier]

    complaint_id = _generate_complaint_id()
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "complaint_id": complaint_id,
        "citizen_id": body.citizen_id,
        "title": body.title,
        "description": body.description,
        "location": body.address or "Not specified",
        "category": category_code,
        "category_label": _human_category(category_code),
        "severity": severity_int,
        "priority_tier": tier,
        "department": department,
        "sla_hours": sla,
        "status": "SUBMITTED",
        "created_at": now,
        "updated_at": now,
    }
    _COMPLAINT_STORE[complaint_id] = record

    return ComplaintResponse(
        id=complaint_id,
        reference_number=complaint_id,
        category=_human_category(category_code),
        category_code=category_code,
        priority=tier,
        department=department,
        status="SUBMITTED",
        sla_hours=sla,
        created_at=now,
        address=body.address,
    )


@router.get("", response_model=list[ComplaintStatusResponse])
async def list_complaints(citizen_id: str):
    """
    List all complaints filed by a citizen in this session.
    Returns newest first.
    """
    records = [
        r for r in _COMPLAINT_STORE.values()
        if r.get("citizen_id") == citizen_id
    ]
    records.sort(key=lambda r: r["created_at"], reverse=True)

    result = []
    for record in records:
        created = datetime.fromisoformat(record["created_at"])
        age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
        status = "ACKNOWLEDGED" if age_minutes > 60 else "SUBMITTED"
        result.append(ComplaintStatusResponse(
            id=record["complaint_id"],
            reference_number=record["complaint_id"],
            category=record.get("category_label", record["category"]),
            priority=record["priority_tier"],
            department=record["department"],
            status=status,
            sla_hours=record["sla_hours"],
            created_at=record["created_at"],
            address=record.get("location"),
        ))
    return result


@router.get("/{complaint_id}", response_model=ComplaintStatusResponse)
async def get_complaint_status(complaint_id: str):
    """
    Retrieve the status of a complaint by its NGR-XXXXXX reference.
    """
    cid = complaint_id.strip().upper()
    record = _COMPLAINT_STORE.get(cid)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No complaint found with ID {complaint_id}.",
        )

    created = datetime.fromisoformat(record["created_at"])
    age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
    status = "ACKNOWLEDGED" if age_minutes > 60 else "SUBMITTED"

    return ComplaintStatusResponse(
        id=record["complaint_id"],
        reference_number=record["complaint_id"],
        category=record.get("category_label", record["category"]),
        priority=record["priority_tier"],
        department=record["department"],
        status=status,
        sla_hours=record["sla_hours"],
        created_at=record["created_at"],
        address=record.get("location"),
    )
