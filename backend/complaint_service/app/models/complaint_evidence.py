import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

class EvidenceType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"

class ComplaintEvidence(Base):
    __tablename__ = "complaint_evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("complaints.id"))
    
    file_url: Mapped[str] = mapped_column(String(1000))
    file_type: Mapped[EvidenceType] = mapped_column(String)
    original_filename: Mapped[str] = mapped_column(String)
    
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="evidence")
