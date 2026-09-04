import datetime
import uuid
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.db.database import Base

class FormSession(Base):
    __tablename__ = "form_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String, index=True, nullable=True)
    schema_id = Column(String, index=True, nullable=False)
    status = Column(String, default="IN_PROGRESS") # IN_PROGRESS, COMPLETED, ABORTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Store the extracted state as JSON for simplicity
    # Format: {"full_name": {"value": "John Doe", "status": "VALID", "confidence": 0.95}}
    state_data = Column(JSON, default=dict)

    # List of currently required missing fields (calculated by schema engine)
    missing_fields = Column(JSON, default=list)

    logs = relationship("ConversationLog", back_populates="session", cascade="all, delete-orphan")

class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("form_sessions.id"))
    role = Column(String) # "user", "agent", "system"
    content = Column(String)
    tool_calls = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("FormSession", back_populates="logs")
