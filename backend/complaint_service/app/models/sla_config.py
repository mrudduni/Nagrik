import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base

class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String)
    severity: Mapped[int] = mapped_column(Integer)
    
    max_acknowledgement_hours: Mapped[int] = mapped_column(Integer)
    max_resolution_hours: Mapped[int] = mapped_column(Integer)
    
    escalation_levels: Mapped[Any] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
