import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.complaint import Complaint
from app.models.sla_config import SLAConfig
from app.services.escalation import EscalationEngine
from app.config import settings

logger = logging.getLogger(__name__)


class SLAMonitor:
    def __init__(self, escalation_engine: Optional[EscalationEngine] = None) -> None:
        self.escalation_engine = escalation_engine or EscalationEngine()

    async def check_sla_compliance(self, db: AsyncSession) -> List[uuid.UUID]:
        """Check for breached SLAs and trigger escalations."""
        escalated_ids = []
        now = datetime.now(timezone.utc)

        query = select(Complaint).where(
            Complaint.status.not_in(["CLOSED", "CITIZEN_VERIFIED"]),
            Complaint.sla_deadline < now,
        )
        result = await db.execute(query)
        breached_complaints = result.scalars().all()

        for complaint in breached_complaints:
            try:
                await self.escalation_engine.escalate(
                    complaint_id=complaint.id,
                    reason=f"SLA Deadline Breached (was due at {complaint.sla_deadline})",
                    db=db,
                )
                escalated_ids.append(complaint.id)
                complaint.sla_deadline = now + timedelta(hours=24)
            except Exception as e:
                logger.error(f"Failed to escalate complaint {complaint.id}: {e}")

        await db.commit()
        return escalated_ids

    async def get_sla_config(self, category: str, severity: int, db: AsyncSession) -> Optional[SLAConfig]:
        """Retrieve SLA configuration for category and severity."""
        query = select(SLAConfig).where(
            and_(
                SLAConfig.category == category,
                SLAConfig.severity == severity,
                SLAConfig.is_active == True,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def set_sla_deadline(self, complaint: Complaint, db: AsyncSession) -> datetime:
        """Set SLA deadline for a complaint based on configured rules or defaults."""
        cat_str = complaint.category.value if hasattr(complaint.category, "value") else str(complaint.category)
        config = await self.get_sla_config(cat_str, complaint.severity or 3, db)

        resolution_hours = config.max_resolution_hours if config else settings.DEFAULT_RESOLUTION_SLA_HOURS

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=resolution_hours)
        complaint.sla_deadline = deadline
        return deadline
