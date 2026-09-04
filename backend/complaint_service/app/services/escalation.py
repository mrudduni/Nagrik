import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.complaint import Complaint
from app.models.complaint_event import ComplaintEvent, EventType
from app.integrations.n8n_client import notify_escalation
from app.config import settings

logger = logging.getLogger(__name__)


class EscalationEngine:
    async def escalate(self, complaint_id: uuid.UUID, reason: str, db: AsyncSession) -> int:
        """Escalate a complaint to the next authority level."""
        query = select(Complaint).where(Complaint.id == complaint_id)
        result = await db.execute(query)
        complaint = result.scalar_one_or_none()

        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        current_level = complaint.escalation_level or 0
        new_level = min(current_level + 1, 3)
        complaint.escalation_level = new_level

        # Create Timeline Event
        event = ComplaintEvent(
            id=uuid.uuid4(),
            complaint_id=complaint.id,
            event_type=EventType.ESCALATED.value,
            actor="SYSTEM",
            details=f"Escalated to level {new_level}. Reason: {reason}",
        )
        db.add(event)

        # Trigger n8n webhook notification
        try:
            await notify_escalation(complaint.id, new_level, reason)
        except Exception as e:
            logger.warning(f"Could not dispatch n8n notification for {complaint_id}: {e}")

        await db.flush()
        return new_level

    async def check_escalation_triggers(self, complaint: Complaint, db: AsyncSession) -> bool:
        """Check if conditions are met to trigger escalation immediately."""
        # 1. Re-opened 2+ times
        reopen_count = await self._get_reopen_count(complaint.id, db)
        if reopen_count >= 2:
            await self.escalate(complaint.id, "Reopened multiple times by citizen", db)
            return True

        # 2. Critical priority with high cluster size
        if complaint.priority_tier == "CRITICAL" and complaint.cluster_id:
            from app.models.complaint_cluster import ComplaintCluster

            c_query = select(ComplaintCluster).where(ComplaintCluster.id == complaint.cluster_id)
            c_res = await db.execute(c_query)
            cluster = c_res.scalar_one_or_none()
            if cluster and cluster.complaint_count >= 5:
                await self.escalate(complaint.id, f"High density critical cluster ({cluster.complaint_count} reports)", db)
                return True

        return False

    async def _get_reopen_count(self, complaint_id: uuid.UUID, db: AsyncSession) -> int:
        query = select(ComplaintEvent).where(
            ComplaintEvent.complaint_id == complaint_id,
            ComplaintEvent.event_type == EventType.REOPENED.value,
        )
        result = await db.execute(query)
        return len(result.scalars().all())
