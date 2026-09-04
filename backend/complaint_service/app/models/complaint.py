import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

class ComplaintCategory(str, Enum):
    POTHOLE = "POTHOLE"
    WATER_SUPPLY = "WATER_SUPPLY"
    DRAINAGE = "DRAINAGE"
    GARBAGE = "GARBAGE"
    STREETLIGHT = "STREETLIGHT"
    POLLUTION = "POLLUTION"
    NOISE = "NOISE"
    ENCROACHMENT = "ENCROACHMENT"
    TRAFFIC = "TRAFFIC"
    ELECTRICITY = "ELECTRICITY"
    PUBLIC_TRANSPORT = "PUBLIC_TRANSPORT"
    SANITATION = "SANITATION"
    OTHER = "OTHER"

class PriorityTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ComplaintStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLUTION_CLAIMED = "RESOLUTION_CLAIMED"
    CITIZEN_VERIFIED = "CITIZEN_VERIFIED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    citizen_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    raw_input: Mapped[str] = mapped_column(Text)
    
    category: Mapped[ComplaintCategory] = mapped_column(String(100))
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    severity: Mapped[int] = mapped_column(Integer)
    priority_score: Mapped[float] = mapped_column(Float)
    priority_tier: Mapped[PriorityTier] = mapped_column(String)
    status: Mapped[ComplaintStatus] = mapped_column(String)
    
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    assigned_officer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("complaint_clusters.id"), nullable=True)
    
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citizen_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="complaints")
    cluster: Mapped[Optional["ComplaintCluster"]] = relationship("ComplaintCluster", foreign_keys=[cluster_id], back_populates="complaints")
    events: Mapped[List["ComplaintEvent"]] = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan")
    evidence: Mapped[List["ComplaintEvidence"]] = relationship("ComplaintEvidence", back_populates="complaint", cascade="all, delete-orphan")
