"""
Core chat endpoints:
  POST /chat        - text (and optionally image attachment) in, text out
  POST /chat/voice   - audio in, audio (+text) out, same underlying graph
  POST /chat/upload  - convenience endpoint for a standalone doc/image upload

All three ultimately drive the same compiled LangGraph graph — modality
handling happens only at the edges (see multilingual/language_boundary.py
and graph/nodes/doc_understanding.py), never inside routing/tools/RAG.
"""
from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, ChatResponse, NavigationAction
from app.graph.build_graph import compiled_graph
from app.graph.nodes.doc_understanding import doc_understanding_node
from app.multilingual.language_boundary import normalize_incoming, prepare_outgoing

router = APIRouter()


async def _run_graph(session_id: str, citizen_id: str, text: str, language: str) -> dict:
    config = {"configurable": {"thread_id": session_id}}
    result = await compiled_graph.ainvoke(
        {
            "messages": [HumanMessage(content=text)],
            "session_id": session_id,
            "citizen_id": citizen_id,
            "language": language,
            "tool_calls_made": [],
        },
        config=config,
    )
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    # If an image/document attachment is present, run doc-understanding
    # first so extracted fields are available to the rest of the graph.
    extracted_fields = {}
    for attachment in payload.attachments:
        if attachment.type in ("image", "document") and attachment.base64_data:
            doc_result = await doc_understanding_node(
                state={"extracted_fields": extracted_fields},
                image_base64=attachment.base64_data,
                mime_type=attachment.mime_type or "image/jpeg",
            )
            extracted_fields.update(doc_result["extracted_fields"])

    incoming_text = payload.message or "(citizen sent an attachment with no text)"

    result = await _run_graph(
        session_id=payload.session_id,
        citizen_id=payload.citizen_id,
        text=incoming_text,
        language=payload.language or "en",
    )

    reply_message = result["messages"][-1]
    nav_dict = result.get("navigation") or {"action": "none"}

    return ChatResponse(
        session_id=payload.session_id,
        reply_text=reply_message.content,
        language=payload.language or "en",
        intent=result.get("intent"),
        navigation=NavigationAction(**nav_dict),
        tool_calls_made=result.get("tool_calls_made", []),
    )


@router.post("/chat/voice", response_model=ChatResponse)
async def chat_voice(payload: ChatRequest):
    """
    Expects payload.attachments to contain one audio attachment
    (base64_data). Runs STT -> pivot-language graph -> translate -> TTS,
    all around the SAME graph used by /chat.
    """
    audio_attachment = next((a for a in payload.attachments if a.type == "audio"), None)
    audio_b64 = audio_attachment.base64_data if audio_attachment else None

    normalized = await normalize_incoming(
        text=payload.message, audio_base64=audio_b64, declared_language=payload.language
    )

    result = await _run_graph(
        session_id=payload.session_id,
        citizen_id=payload.citizen_id,
        text=normalized["text"],
        language=normalized["original_language"],
    )

    reply_message = result["messages"][-1]
    outgoing = await prepare_outgoing(
        reply_text_en=reply_message.content,
        target_language=normalized["original_language"],
        want_audio=True,
    )

    nav_dict = result.get("navigation") or {"action": "none"}

    return ChatResponse(
        session_id=payload.session_id,
        reply_text=outgoing["text"],
        reply_audio_base64=outgoing["audio_base64"],
        language=normalized["original_language"],
        intent=result.get("intent"),
        navigation=NavigationAction(**nav_dict),
        tool_calls_made=result.get("tool_calls_made", []),
    )
