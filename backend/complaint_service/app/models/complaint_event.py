import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

class EventType(str, Enum):
    CREATED = "CREATED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    ACTION_TAKEN = "ACTION_TAKEN"
    RESOLUTION_CLAIMED = "RESOLUTION_CLAIMED"
    CITIZEN_VERIFIED = "CITIZEN_VERIFIED"
    CITIZEN_REJECTED = "CITIZEN_REJECTED"
    REOPENED = "REOPENED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"
    COMMENT = "COMMENT"

class ComplaintEvent(Base):
    __tablename__ = "complaint_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("complaints.id"))
    
    event_type: Mapped[EventType] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="events")
