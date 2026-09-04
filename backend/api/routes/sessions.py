from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.db.database import get_db
from backend.db.models import FormSession

router = APIRouter()

# ---------- Pydantic models ----------

class CreateSessionRequest(BaseModel):
    schema_id: str
    phone_number: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    schema_id: str
    status: str
    state_data: Dict[str, Any]
    missing_fields: list

class ChatRequest(BaseModel):
    session_id: str
    text: str
    schema_id: Optional[str] = "aadhaar_enrolment_form1"

class ChatResponse(BaseModel):
    response: str
    is_complete: bool
    data: Dict[str, Any]

# ---------- Endpoints ----------

@router.post("/", response_model=SessionResponse)
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    db_session = FormSession(
        schema_id=req.schema_id,
        phone_number=req.phone_number,
        state_data={},
        missing_fields=[]
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(FormSession).filter(FormSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.post("/chat", response_model=ChatResponse)
def chat_api(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Main conversational endpoint used by the Web UI.
    - Auto-creates a session for the given session_id if one doesn't exist.
    - Routes the user message through the FormAgent (Gemini + tools).
    - Returns the agent's response plus form completion status.
    """
    db_session = db.query(FormSession).filter(FormSession.id == req.session_id).first()

    # Auto-create session on first message (for ease of web UI usage)
    if not db_session:
        db_session = FormSession(
            id=req.session_id,
            schema_id=req.schema_id,
            state_data={},
            missing_fields=[]
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    # Lazy import to avoid circular imports at module load time
    from backend.agents.form_agent import FormAgent

    agent = FormAgent(db, db_session.id)
    response_text = agent.process_message(req.text)

    # Refresh DB object to get latest state after agent tool calls
    db.refresh(db_session)

    missing = agent.state_manager.get_missing_fields()
    unconfirmed = [
        k for k, v in db_session.state_data.items()
        if isinstance(v, dict) and v.get("status") == "UNCONFIRMED"
    ]
    is_complete = len(missing) == 0 and len(unconfirmed) == 0

    if is_complete:
        db_session.status = "COMPLETED"
        db.commit()

    return {
        "response": response_text,
        "is_complete": is_complete,
        "data": db_session.state_data,
    }
