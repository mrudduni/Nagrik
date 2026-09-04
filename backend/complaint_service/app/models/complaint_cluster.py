import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

class ClusterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class ComplaintCluster(Base):
    __tablename__ = "complaint_clusters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    representative_complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("complaints.id", use_alter=True), nullable=True)
    
    category: Mapped[str] = mapped_column(String)
    centroid_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    centroid_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ClusterStatus] = mapped_column(String)
    avg_severity: Mapped[float] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", foreign_keys="Complaint.cluster_id", back_populates="cluster")
    representative_complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", foreign_keys=[representative_complaint_id])
