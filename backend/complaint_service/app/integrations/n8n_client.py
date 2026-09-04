import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class N8NClient:
    """Client for dispatching notifications to n8n webhook workflows."""

    def __init__(self):
        self.webhook_url = settings.N8N_WEBHOOK_URL

    async def send_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        if not self.webhook_url:
            logger.debug(f"n8n webhook URL not configured; skipping {event_type}")
            return False

        data = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(self.webhook_url, json=data)
                response.raise_for_status()
                logger.info(f"Dispatched n8n webhook for {event_type}")
                return True
        except Exception as exc:
            logger.warning(f"Failed to post to n8n webhook ({event_type}): {exc}")
            return False


async def notify_escalation(complaint_id: Union[str, uuid.UUID], level: int, reason: str) -> bool:
    client = N8NClient()
    return await client.send_webhook(
        "ESCALATION",
        {
            "complaint_id": str(complaint_id),
            "escalation_level": level,
            "reason": reason,
        },
    )


async def notify_sla_breach(complaint_id: Union[str, uuid.UUID], department: str) -> bool:
    client = N8NClient()
    return await client.send_webhook(
        "SLA_BREACH",
        {
            "complaint_id": str(complaint_id),
            "department": department,
        },
    )


async def notify_status_change(complaint_id: Union[str, uuid.UUID], old_status: str, new_status: str) -> bool:
    client = N8NClient()
    return await client.send_webhook(
        "STATUS_UPDATE",
        {
            "complaint_id": str(complaint_id),
            "old_status": old_status,
            "new_status": new_status,
        },
    )
