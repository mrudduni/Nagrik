"""
Complaint API Routes — Full CRUD + pipeline for citizen complaints.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.complaint_event import ComplaintEvent
from app.models.complaint_evidence import ComplaintEvidence
from app.models.department import Department
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusResponse,
    ComplaintListResponse,
    ComplaintUpdate,
    ComplaintVerification,
)
from app.schemas.cluster import DuplicateCheckResult
from app.services.classifier import ComplaintClassifier
from app.services.duplicate_detector import DuplicateDetector
from app.services.priority_scorer import PriorityScorer
from app.services.router import DepartmentRouter
from app.services.resolution import ResolutionTracker
from app.services.sla_monitor import SLAMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["Complaints"])

# ── Singleton-ish service instances ───────────────────────────────────────────
_classifier: ComplaintClassifier | None = None


def _get_classifier() -> ComplaintClassifier:
    global _classifier
    if _classifier is None:
        _classifier = ComplaintClassifier()
    return _classifier


# ── Helper: build ComplaintResponse from ORM object ──────────────────────────
def _to_response(c: Complaint) -> dict:
    dept_name = c.department.name if c.department else None
    evidence_urls = [e.file_url for e in c.evidence] if c.evidence else []
    return {
        "id": c.id,
        "citizen_id": c.citizen_id,
        "title": c.title,
        "description": c.description,
        "raw_input": c.raw_input,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "ward": c.ward,
        "district": c.district,
        "state": c.state,
        "evidence_urls": evidence_urls,
        "category": c.category,
        "sub_category": c.sub_category,
        "severity": c.severity,
        "priority_tier": c.priority_tier,
        "priority_score": c.priority_score,
        "status": c.status,
        "department_code": c.department.code if c.department else None,
        "assigned_officer": c.assigned_officer,
        "cluster_id": c.cluster_id,
        "escalation_level": c.escalation_level,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "sla_deadline": c.sla_deadline,
        "resolved_at": None,
    }


# ── 1. Submit new complaint ──────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    complaint_in: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Full complaint pipeline:
    classify → check duplicates → calculate priority → route → set SLA → persist.
    """
    # 1 — Classify
    classifier = _get_classifier()
    classification = await classifier.classify(complaint_in.description)
    logger.info(f"Classified as {classification.category} (sev={classification.severity})")

    # 2 — Route to department
    dept_router = DepartmentRouter()
    department = await dept_router.route_complaint(
        classification.category, complaint_in.state, complaint_in.district, db
    )

    # 3 — Check duplicates
    from app.main import get_embedding_service  # avoid circular at module level

    embedding_svc = get_embedding_service()
    detector = DuplicateDetector(embedding_svc)
    dup_result = await detector.detect_duplicates(
        complaint_in.description,
        classification.category,
        complaint_in.latitude,
        complaint_in.longitude,
        db,
    )

    # 4 — Priority scoring
    scorer = PriorityScorer()
    cluster_size = (
        len(dup_result.similar_complaints)
        if dup_result.suggested_cluster_id
        else 0
    )
    priority_score, priority_tier = await scorer.calculate_priority(
        severity=classification.severity, cluster_size=cluster_size
    )

    # 5 — Create complaint record
    complaint = Complaint(
        id=uuid.uuid4(),
        citizen_id=complaint_in.citizen_id,
        title=complaint_in.title,
        description=complaint_in.description,
        raw_input=complaint_in.raw_input or complaint_in.description,
        category=classification.category,
        sub_category=classification.sub_category,
        severity=classification.severity,
        priority_score=priority_score,
        priority_tier=priority_tier,
        status=ComplaintStatus.SUBMITTED.value,
        department_id=department.id if department else None,
        latitude=complaint_in.latitude,
        longitude=complaint_in.longitude,
        ward=complaint_in.ward,
        district=complaint_in.district,
        state=complaint_in.state,
        cluster_id=dup_result.suggested_cluster_id,
        escalation_level=0,
    )

    # 6 — Set SLA deadline
    sla_monitor = SLAMonitor()
    await sla_monitor.set_sla_deadline(complaint, db)

    # 7 — Create CREATED event
    event = ComplaintEvent(
        id=uuid.uuid4(),
        complaint_id=complaint.id,
        event_type="CREATED",
        actor="system",
        details=f"Complaint submitted. Category={classification.category}, Severity={classification.severity}",
    )

    db.add(complaint)
    db.add(event)

    # 8 — Handle evidence URLs
    if complaint_in.evidence_urls:
        for url in complaint_in.evidence_urls:
            evidence = ComplaintEvidence(
                id=uuid.uuid4(),
                complaint_id=complaint.id,
                file_url=url,
                file_type="IMAGE",
                original_filename=url.split("/")[-1],
            )
            db.add(evidence)

    await db.commit()
    await db.refresh(complaint, ["department", "evidence"])

    # 9 — Add to FAISS index (non-blocking)
    try:
        embedding_svc.add_to_index(str(complaint.id), complaint.description)
        embedding_svc.save_index()
    except Exception as exc:
        logger.warning(f"Failed to index complaint in FAISS: {exc}")

    return {
        "complaint_id": str(complaint.id),
        "status": complaint.status,
        "category": complaint.category,
        "severity": complaint.severity,
        "priority_tier": complaint.priority_tier,
        "department": department.name if department else None,
        "is_duplicate": dup_result.is_duplicate,
        "similar_count": len(dup_result.similar_complaints),
        "sla_deadline": complaint.sla_deadline.isoformat() if complaint.sla_deadline else None,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
    }


# ── 2. Get complaint detail ──────────────────────────────────────────────────
@router.get("/{complaint_id}")
async def get_complaint(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """Get full complaint detail with events and evidence."""
    uid = uuid.UUID(complaint_id)
    stmt = (
        select(Complaint)
        .options(
            selectinload(Complaint.department),
            selectinload(Complaint.events),
            selectinload(Complaint.evidence),
        )
        .where(Complaint.id == uid)
    )
    result = await db.execute(stmt)
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _to_response(complaint)


# ── 3. Lightweight status ────────────────────────────────────────────────────
@router.get("/{complaint_id}/status")
async def get_complaint_status(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """Lightweight status endpoint for Person 2's agent."""
    uid = uuid.UUID(complaint_id)
    stmt = (
        select(Complaint)
        .options(selectinload(Complaint.department), selectinload(Complaint.events))
        .where(Complaint.id == uid)
    )
    result = await db.execute(stmt)
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    last_event = None
    if complaint.events:
        last_event = sorted(complaint.events, key=lambda e: e.created_at)[-1].event_type

    return ComplaintStatusResponse(
        complaint_id=complaint.id,
        status=complaint.status,
        department=complaint.department.name if complaint.department else None,
        priority_tier=complaint.priority_tier,
        escalation_level=complaint.escalation_level,
        created_at=complaint.created_at,
        sla_deadline=complaint.sla_deadline,
        last_event=last_event,
    )


# ── 4. List / filter complaints ──────────────────────────────────────────────
@router.get("/")
async def list_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    severity: Optional[int] = None,
    department_id: Optional[str] = None,
    citizen_id: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    """List complaints with filtering and pagination."""
    stmt = select(Complaint).options(selectinload(Complaint.department))

    # Filters
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if category:
        stmt = stmt.where(Complaint.category == category)
    if severity:
        stmt = stmt.where(Complaint.severity == severity)
    if department_id:
        stmt = stmt.where(Complaint.department_id == uuid.UUID(department_id))
    if citizen_id:
        stmt = stmt.where(Complaint.citizen_id == citizen_id)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(Complaint, sort_by, Complaint.created_at)
    stmt = stmt.order_by(desc(sort_col) if sort_order == "desc" else asc(sort_col))

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    complaints = result.scalars().all()

    return {
        "items": [_to_response(c) for c in complaints],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ── 5. Update status (authority side) ────────────────────────────────────────
@router.patch("/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    update_in: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Authority-side status update using the resolution state machine."""
    uid = uuid.UUID(complaint_id)
    tracker = ResolutionTracker()

    if update_in.status:
        complaint = await tracker.transition(
            uid, update_in.status, actor="authority", details=update_in.resolution_notes, db=db
        )
    else:
        raise HTTPException(status_code=400, detail="Status is required")

    if update_in.assigned_officer:
        complaint.assigned_officer = update_in.assigned_officer
        await db.commit()
        await db.refresh(complaint)

    return {"complaint_id": str(complaint.id), "status": complaint.status}


# ── 6. Citizen verification ──────────────────────────────────────────────────
@router.post("/{complaint_id}/verify")
async def verify_resolution(
    complaint_id: str,
    verification: ComplaintVerification,
    db: AsyncSession = Depends(get_db),
):
    """Citizen accepts or rejects the claimed resolution."""
    uid = uuid.UUID(complaint_id)
    tracker = ResolutionTracker()
    complaint = await tracker.verify_resolution(
        uid, verification.accepted, verification.feedback, db
    )
    return {
        "complaint_id": str(complaint.id),
        "status": complaint.status,
        "accepted": verification.accepted,
    }


# ── 7. Add evidence ──────────────────────────────────────────────────────────
@router.post("/{complaint_id}/evidence", status_code=status.HTTP_201_CREATED)
async def add_evidence(
    complaint_id: str,
    file_url: str,
    file_type: str = "IMAGE",
    original_filename: str = "uploaded_file",
    db: AsyncSession = Depends(get_db),
):
    """Attach evidence to a complaint."""
    uid = uuid.UUID(complaint_id)
    # Verify complaint exists
    complaint = (await db.execute(select(Complaint).where(Complaint.id == uid))).scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    evidence = ComplaintEvidence(
        id=uuid.uuid4(),
        complaint_id=uid,
        file_url=file_url,
        file_type=file_type,
        original_filename=original_filename,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return {"id": str(evidence.id), "complaint_id": str(uid), "file_url": evidence.file_url}


# ── 8. Event timeline ────────────────────────────────────────────────────────
@router.get("/{complaint_id}/timeline")
async def get_timeline(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """Get event timeline for a complaint."""
    uid = uuid.UUID(complaint_id)
    stmt = (
        select(ComplaintEvent)
        .where(ComplaintEvent.complaint_id == uid)
        .order_by(ComplaintEvent.created_at)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor": e.actor,
            "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


# ── 9. Similar complaints ────────────────────────────────────────────────────
@router.get("/{complaint_id}/similar")
async def get_similar_complaints(
    complaint_id: str, db: AsyncSession = Depends(get_db)
):
    """Find similar/duplicate complaints."""
    uid = uuid.UUID(complaint_id)
    complaint = (
        await db.execute(select(Complaint).where(Complaint.id == uid))
    ).scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    from app.main import get_embedding_service

    embedding_svc = get_embedding_service()
    detector = DuplicateDetector(embedding_svc)
    result = await detector.detect_duplicates(
        complaint.description,
        complaint.category,
        complaint.latitude,
        complaint.longitude,
        db,
    )
    return result
