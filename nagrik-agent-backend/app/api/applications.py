"""
Application status/lookup endpoints, and the entry point for the
form-filling flow. Kept separate from /chat's main graph invocation for
clarity, but reuses the same AgentState shape and get_llm() abstraction.
"""
from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.forms import SAMPLE_SCHOLARSHIP_FORM
from app.graph.nodes.form_filler import form_filler_node

router = APIRouter()

# In-memory demo store of per-session extracted fields.
# Replace with the checkpointer/DB-backed state in a real deployment.
_SESSION_FIELDS: dict[str, dict] = {}


@router.post("/applications/scholarship/continue", response_model=ChatResponse)
async def continue_scholarship_application(payload: ChatRequest):
    state = {
        "messages": [HumanMessage(content=payload.message or "")],
        "extracted_fields": _SESSION_FIELDS.get(payload.session_id, {}),
    }

    result = await form_filler_node(state, form_schema=SAMPLE_SCHOLARSHIP_FORM)
    _SESSION_FIELDS[payload.session_id] = result["extracted_fields"]

    reply_message = result["messages"][-1]
    return ChatResponse(
        session_id=payload.session_id,
        reply_text=reply_message.content,
        language=payload.language or "en",
        intent="application",
    )
