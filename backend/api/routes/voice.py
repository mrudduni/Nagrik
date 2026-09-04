from fastapi import APIRouter, Request, Depends, Form
from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import FormSession

router = APIRouter()

DEFAULT_SCHEMA = "aadhaar_enrolment_form1"

@router.post("/voice")
async def voice_entry(
    request: Request,
    CallSid: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Twilio entry-point: initialise session, speak first prompt via agent."""
    db_session = db.query(FormSession).filter(FormSession.id == CallSid).first()
    if not db_session:
        db_session = FormSession(
            id=CallSid,
            schema_id=DEFAULT_SCHEMA,
            state_data={},
            missing_fields=[],
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    from backend.agents.form_agent import FormAgent
    agent = FormAgent(db, db_session.id)
    # Empty first message → agent introduces itself and asks first question
    first_prompt = agent.process_message("")

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/api/twilio/gather",
        speechTimeout="auto",
        language="en-IN",
    )
    gather.say(first_prompt, language="en-IN")
    response.append(gather)
    response.say("We didn't receive any input. Goodbye!", language="en-IN")
    return str(response)


@router.post("/gather")
async def gather_input(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Twilio speech gather: pass transcript to agent, speak response."""
    db_session = db.query(FormSession).filter(FormSession.id == CallSid).first()
    response = VoiceResponse()

    if not db_session:
        response.say("Your session has expired. Please call again.")
        response.hangup()
        return str(response)

    from backend.agents.form_agent import FormAgent
    agent = FormAgent(db, db_session.id)
    reply = agent.process_message(SpeechResult)

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
        response.say(reply, language="en-IN")
        response.hangup()
        return str(response)

    gather = Gather(
        input="speech",
        action="/api/twilio/gather",
        speechTimeout="auto",
        language="en-IN",
    )
    gather.say(reply, language="en-IN")
    response.append(gather)
    response.say("We didn't receive any input. Goodbye!", language="en-IN")
    return str(response)

