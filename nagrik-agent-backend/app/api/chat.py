"""
Core chat endpoints:
  POST /chat        - text (and optionally image attachment) in, text out
  POST /chat/voice   - audio in, audio (+text) out, same underlying graph
  POST /chat/upload  - convenience endpoint for a standalone doc/image upload

All three ultimately drive the same compiled LangGraph graph — modality
handling happens only at the edges (see multilingual/language_boundary.py
and graph/nodes/doc_understanding.py), never inside routing/tools/RAG.
"""
import ast
import json

from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, ChatResponse, ChatSource, NavigationAction
from app.graph.build_graph import compiled_graph
from app.graph.nodes.doc_understanding import doc_understanding_node
from app.multilingual.language_boundary import normalize_incoming, prepare_outgoing

router = APIRouter()


def _build_graph_text(message: str, extracted_text: str, extracted_fields: dict) -> str:
    parts = [message.strip() or "(citizen sent an attachment with no text)"]
    if extracted_text:
        parts.append(f"Extracted document text:\n{extracted_text.strip()}")
    if extracted_fields:
        parts.append(f"Extracted document fields:\n{json.dumps(extracted_fields, ensure_ascii=False)}")
    return "\n\n".join(parts)


def _coerce_tool_payload(content) -> dict | None:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(content)
        except (ValueError, SyntaxError):
            return None
    return parsed if isinstance(parsed, dict) else None


def _extract_sources(result: dict) -> list[ChatSource]:
    sources: list[ChatSource] = []
    seen = set()

    for message in result.get("messages", []):
        if getattr(message, "name", None) != "tree_rag_search":
            continue
        payload = _coerce_tool_payload(message.content)
        if not payload or not payload.get("found"):
            continue

        for chunk in payload.get("chunks", []):
            key = (
                chunk.get("scheme"),
                chunk.get("source_file"),
                chunk.get("source_url"),
                chunk.get("page"),
            )
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                ChatSource(
                    scheme=chunk.get("scheme"),
                    ministry=chunk.get("ministry"),
                    department=chunk.get("department"),
                    source_file=chunk.get("source_file"),
                    source_url=chunk.get("source_url"),
                    page=chunk.get("page"),
                    snippet=(chunk.get("text") or "")[:300],
                )
            )

    return sources


async def _collect_attachment_context(payload: ChatRequest) -> dict:
    extracted_fields = {}
    extracted_text_parts: list[str] = []

    for attachment in payload.attachments:
        if attachment.type not in ("image", "document") or not attachment.base64_data:
            continue

        doc_result = await doc_understanding_node(
            state={"extracted_fields": extracted_fields},
            image_base64=attachment.base64_data,
            mime_type=attachment.mime_type or "image/jpeg",
        )
        extracted_fields.update(doc_result.get("extracted_fields", {}))
        if doc_result.get("extracted_text"):
            extracted_text_parts.append(doc_result["extracted_text"])

    return {
        "extracted_fields": extracted_fields,
        "extracted_text": "\n\n".join(extracted_text_parts),
    }


async def _run_graph(
    session_id: str,
    citizen_id: str,
    text: str,
    language: str,
    original_message: str,
    extracted_fields: dict | None = None,
    extracted_text: str = "",
) -> dict:
    config = {"configurable": {"thread_id": session_id}}
    result = await compiled_graph.ainvoke(
        {
            "messages": [HumanMessage(content=text)],
            "session_id": session_id,
            "citizen_id": citizen_id,
            "language": language,
            "normalized_query": text,
            "original_message": original_message,
            "extracted_fields": extracted_fields or {},
            "extracted_text": extracted_text,
            "tool_calls_made": [],
            "sources": [],
        },
        config=config,
    )
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    attachment_context = await _collect_attachment_context(payload)
    normalized = await normalize_incoming(
        text=payload.message,
        audio_base64=None,
        declared_language=payload.language,
    )
    graph_text = _build_graph_text(
        normalized["text"],
        attachment_context["extracted_text"],
        attachment_context["extracted_fields"],
    )

    result = await _run_graph(
        session_id=payload.session_id,
        citizen_id=payload.citizen_id,
        text=graph_text,
        language=normalized["original_language"],
        original_message=normalized["original_text"],
        extracted_fields=attachment_context["extracted_fields"],
        extracted_text=attachment_context["extracted_text"],
    )

    reply_message = result["messages"][-1]
    outgoing = await prepare_outgoing(
        reply_text_en=reply_message.content,
        target_language=normalized["original_language"],
        want_audio=False,
    )
    nav_dict = result.get("navigation") or {"action": "none"}

    return ChatResponse(
        session_id=payload.session_id,
        reply_text=outgoing["text"],
        language=normalized["original_language"],
        intent=result.get("intent"),
        navigation=NavigationAction(**nav_dict),
        tool_calls_made=result.get("tool_calls_made", []),
        sources=_extract_sources(result),
        extracted_fields=attachment_context["extracted_fields"],
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

    attachment_context = await _collect_attachment_context(payload)
    normalized = await normalize_incoming(
        text=payload.message, audio_base64=audio_b64, declared_language=payload.language
    )
    graph_text = _build_graph_text(
        normalized["text"],
        attachment_context["extracted_text"],
        attachment_context["extracted_fields"],
    )

    result = await _run_graph(
        session_id=payload.session_id,
        citizen_id=payload.citizen_id,
        text=graph_text,
        language=normalized["original_language"],
        original_message=normalized["original_text"],
        extracted_fields=attachment_context["extracted_fields"],
        extracted_text=attachment_context["extracted_text"],
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
        sources=_extract_sources(result),
        extracted_fields=attachment_context["extracted_fields"],
    )
