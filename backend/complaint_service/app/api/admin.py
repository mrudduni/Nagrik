import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from pydantic import BaseModel

from app.database import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.services.resolution import ResolutionTracker

router = APIRouter(prefix="/admin", tags=["Admin"])


class AssignRequest(BaseModel):
    officer_name: str


class ResolveRequest(BaseModel):
    resolution_notes: str


@router.post("/complaints/{complaint_id}/acknowledge")
async def acknowledge_complaint(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Mark a complaint as acknowledged by the municipal authority."""
    tracker = ResolutionTracker()
    try:
        complaint = await tracker.transition(
            complaint_id=complaint_id,
            new_status="ACKNOWLEDGED",
            actor="OFFICER",
            details="Complaint acknowledged by departmental officer.",
            db=db,
        )
        return {
            "status": "success",
            "complaint_id": str(complaint.id),
            "current_status": complaint.status,
            "message": "Complaint marked as acknowledged.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/complaints/{complaint_id}/assign")
async def assign_complaint(
    complaint_id: uuid.UUID,
    payload: AssignRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign a complaint to a specific field officer or engineer."""
    tracker = ResolutionTracker()
    try:
        complaint = await tracker.transition(
            complaint_id=complaint_id,
            new_status="ASSIGNED",
            actor="OFFICER",
            details=f"Assigned to officer {payload.officer_name}",
            db=db,
        )
        complaint.assigned_officer = payload.officer_name
        await db.commit()
        await db.refresh(complaint)

        return {
            "status": "success",
            "complaint_id": str(complaint.id),
            "assigned_officer": complaint.assigned_officer,
            "current_status": complaint.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/complaints/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: uuid.UUID,
    payload: ResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Claim resolution for a complaint and trigger citizen verification."""
    tracker = ResolutionTracker()
    try:
        complaint = await tracker.transition(
            complaint_id=complaint_id,
            new_status="RESOLUTION_CLAIMED",
            actor="OFFICER",
            details=payload.resolution_notes,
            db=db,
        )
        complaint.resolution_notes = payload.resolution_notes
        await db.commit()
        await db.refresh(complaint)

        return {
            "status": "success",
            "complaint_id": str(complaint.id),
            "current_status": complaint.status,
            "resolution_notes": complaint.resolution_notes,
            "message": "Resolution claimed. Awaiting citizen verification.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/queue")
async def get_department_queue(
    department_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """View the queue of open/actionable complaints for a specific department."""
    query = (
        select(Complaint)
        .where(
            Complaint.department_id == department_id,
            Complaint.status.not_in(["CLOSED", "CITIZEN_VERIFIED"]),
        )
        .order_by(desc(Complaint.priority_score), Complaint.created_at)
        .limit(limit)
    )
    result = await db.execute(query)
    complaints = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "category": c.category,
            "severity": c.severity,
            "priority_tier": c.priority_tier,
            "priority_score": c.priority_score,
            "status": c.status,
            "assigned_officer": c.assigned_officer,
            "escalation_level": c.escalation_level,
            "sla_deadline": c.sla_deadline.isoformat() if c.sla_deadline else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complaints
    ]


@router.get("/health")
async def admin_health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )
