import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.complaint import Complaint, ComplaintStatus
from app.models.complaint_event import ComplaintEvent, EventType
from app.services.escalation import EscalationEngine
from app.integrations.n8n_client import notify_status_change

logger = logging.getLogger(__name__)


class ResolutionTracker:
    VALID_TRANSITIONS = {
        "SUBMITTED": ["ACKNOWLEDGED", "ASSIGNED", "CLOSED"],
        "ACKNOWLEDGED": ["ASSIGNED", "IN_PROGRESS"],
        "ASSIGNED": ["IN_PROGRESS", "ACKNOWLEDGED"],
        "IN_PROGRESS": ["RESOLUTION_CLAIMED"],
        "RESOLUTION_CLAIMED": ["CITIZEN_VERIFIED", "REOPENED"],
        "REOPENED": ["ASSIGNED", "IN_PROGRESS", "ESCALATED"],
        "CITIZEN_VERIFIED": ["CLOSED"],
        "CLOSED": [],
    }

    def __init__(self, escalation_engine: Optional[EscalationEngine] = None) -> None:
        self.escalation_engine = escalation_engine or EscalationEngine()

    async def transition(
        self,
        complaint_id: uuid.UUID,
        new_status: str,
        actor: str,
        details: Optional[str],
        db: AsyncSession,
    ) -> Complaint:
        query = select(Complaint).where(Complaint.id == complaint_id)
        result = await db.execute(query)
        complaint = result.scalar_one_or_none()

        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        current_status = complaint.status.value if hasattr(complaint.status, "value") else str(complaint.status)
        new_status_str = new_status.value if hasattr(new_status, "value") else str(new_status)

        # 1. Validate transition
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if new_status_str not in allowed and new_status_str != current_status:
            raise ValueError(f"Invalid state transition from {current_status} to {new_status_str}")

        old_status = complaint.status
        complaint.status = new_status_str

        # 2. Add event to timeline
        event = ComplaintEvent(
            id=uuid.uuid4(),
            complaint_id=complaint.id,
            event_type=new_status_str,
            actor=actor,
            details=details or f"Status changed to {new_status_str}",
        )
        db.add(event)

        # 3. Notify via n8n
        try:
            await notify_status_change(complaint.id, str(old_status), new_status_str)
        except Exception as e:
            logger.warning(f"Failed to send status update notification: {e}")

        await db.commit()
        await db.refresh(complaint)
        return complaint

    async def verify_resolution(
        self,
        complaint_id: uuid.UUID,
        accepted: bool,
        feedback: Optional[str],
        db: AsyncSession,
    ) -> Complaint:
        query = select(Complaint).where(Complaint.id == complaint_id)
        result = await db.execute(query)
        complaint = result.scalar_one_or_none()

        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        curr_status = complaint.status.value if hasattr(complaint.status, "value") else str(complaint.status)
        if curr_status != "RESOLUTION_CLAIMED":
            raise ValueError(f"Complaint is not awaiting verification (current status: {curr_status})")

        actor = str(complaint.citizen_id) if complaint.citizen_id else "CITIZEN"

        if accepted:
            complaint.citizen_feedback = feedback
            complaint = await self.transition(complaint.id, "CITIZEN_VERIFIED", actor, feedback, db)
            complaint = await self.transition(complaint.id, "CLOSED", "SYSTEM", "Auto-closed following citizen acceptance", db)
        else:
            complaint.citizen_feedback = feedback
            complaint = await self.transition(complaint.id, "REOPENED", actor, f"Rejected by citizen: {feedback}", db)
            await self.escalation_engine.check_escalation_triggers(complaint, db)

        return complaint
