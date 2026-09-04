import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any

from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class JurisdictionLevel(str, Enum):
    MUNICIPAL = "MUNICIPAL"
    DISTRICT = "DISTRICT"
    STATE = "STATE"
    CENTRAL = "CENTRAL"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    jurisdiction_level: Mapped[str] = mapped_column(String)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"), nullable=True)

    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    issue_categories: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="department")

    children: Mapped[List["Department"]] = relationship("Department", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["Department"]] = relationship("Department", back_populates="children", remote_side=[id])
