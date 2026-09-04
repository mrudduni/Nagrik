"""
Core chat endpoints:
  POST /chat        – text (and optionally image/document attachment) in, text out
  POST /chat/voice  – audio in, audio (+text) out, same underlying graph
  POST /chat/upload – convenience wrapper for standalone doc/image upload

All three drive the same compiled LangGraph graph.  Modality handling
(STT, OCR, PDF extraction) happens only at the edges, never inside
routing/tools/RAG.

Validation rules applied here:
  - message and/or attachment must be present
  - attachment base64 must not be empty
  - attachment MIME type must be supported
  - audio_base64 must be present on /chat/voice
  - payloads larger than MAX_ATTACHMENT_B64_LEN are rejected
  - base64 payload is never echoed back in error messages or logs
"""
import ast
import json
import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, ChatResponse, ChatSource, NavigationAction
from app.graph.build_graph import compiled_graph
from app.graph.nodes.doc_understanding import doc_understanding_node
from app.multilingual.language_boundary import normalize_incoming, prepare_outgoing

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Constants ────────────────────────────────────────────────────────────────

# 10 MB of raw data ≈ ~13.3 MB base64 — generous limit for a single attachment
MAX_ATTACHMENT_B64_LEN = 14_000_000  # chars

ALLOWED_IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/heic", "image/heif",
}
ALLOWED_DOCUMENT_MIMES = {"application/pdf"}

ALLOWED_AUDIO_MIMES = {
    "audio/webm", "audio/mp4", "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp3", "audio/m4a", "audio/ogg",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_graph_text(
    message: str, extracted_text: str, extracted_fields: dict
) -> str:
    parts = [message.strip() or "(citizen sent an attachment with no text)"]
    if extracted_text:
        parts.append(f"Extracted document text:\n{extracted_text.strip()}")
    if extracted_fields:
        parts.append(
            f"Extracted document fields:\n{json.dumps(extracted_fields, ensure_ascii=False)}"
        )
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
    seen: set = set()

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

            # Sanitise source_file — never expose local paths
            source_file = chunk.get("source_file") or ""
            if any(
                x in source_file
                for x in (":\\", "/data/", "chroma", "./", "/app/")
            ):
                source_file = None
            else:
                # Keep only the filename, not any directory prefix
                import os
                source_file = os.path.basename(source_file) if source_file else None

            sources.append(
                ChatSource(
                    scheme=chunk.get("scheme"),
                    ministry=chunk.get("ministry"),
                    department=chunk.get("department"),
                    source_file=source_file,
                    source_url=chunk.get("source_url"),
                    page=chunk.get("page"),
                    snippet=(chunk.get("text") or "")[:300],
                )
            )

    return sources


def _validate_attachment(attachment) -> None:
    """Raise HTTPException for invalid attachments."""
    if not attachment.base64_data:
        raise HTTPException(
            status_code=400,
            detail="Attachment is missing base64_data.",
        )

    if len(attachment.base64_data) > MAX_ATTACHMENT_B64_LEN:
        raise HTTPException(
            status_code=413,
            detail=(
                "Attachment exceeds the maximum allowed size (approx. 10 MB). "
                "Please send a smaller file."
            ),
        )

    mime = (attachment.mime_type or "").lower().strip()

    if attachment.type == "image":
        if not mime.startswith("image/"):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported image MIME type: '{mime}'. "
                       f"Supported: {sorted(ALLOWED_IMAGE_MIMES)}",
            )
    elif attachment.type == "document":
        if mime not in ALLOWED_DOCUMENT_MIMES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported document MIME type: '{mime}'. "
                       f"Only PDF (application/pdf) is supported.",
            )
    elif attachment.type == "audio":
        if mime not in ALLOWED_AUDIO_MIMES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported audio MIME type: '{mime}'.",
            )


async def _collect_attachment_context(payload: ChatRequest) -> dict:
    extracted_fields: dict = {}
    extracted_text_parts: list[str] = []

    if not payload.attachments:
        return {"extracted_fields": {}, "extracted_text": ""}

    for attachment in payload.attachments:
        if attachment.type not in ("image", "document"):
            logger.debug("Skipping unsupported attachment type: %s", attachment.type)
            continue

        # Validate before processing
        try:
            _validate_attachment(attachment)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid attachment: {exc}"
            ) from exc

        mime_type = (attachment.mime_type or "image/jpeg").lower()

        try:
            doc_result = await doc_understanding_node(
                state={"extracted_fields": extracted_fields},
                image_base64=attachment.base64_data,
                mime_type=mime_type,
            )
            extracted_fields.update(doc_result.get("extracted_fields", {}))
            if doc_result.get("extracted_text"):
                extracted_text_parts.append(doc_result["extracted_text"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.warning("Document understanding failed: %s", repr(exc))
            # Non-fatal: continue without extracted content

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


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    # At least a message or an attachment must be present
    if not payload.message and not payload.attachments:
        raise HTTPException(
            status_code=400,
            detail="Request must include either 'message' text or an attachment.",
        )

    try:
        attachment_context = await _collect_attachment_context(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Attachment processing error: %s", repr(exc))
        raise HTTPException(
            status_code=422,
            detail="Could not process the attachment. Please try a different file.",
        ) from exc

    try:
        normalized = await normalize_incoming(
            text=payload.message,
            audio_base64=None,
            declared_language=payload.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_text = normalized["text"]

    # If the citizen uploaded a file without any text prompt, synthesize one
    if (
        not payload.message
        and payload.attachments
        and attachment_context["extracted_text"]
    ):
        user_text = (
            "Analyze the uploaded attachment and explain "
            "the important information to the citizen."
        )

    graph_text = _build_graph_text(
        user_text,
        attachment_context["extracted_text"],
        attachment_context["extracted_fields"],
    )

    try:
        result = await _run_graph(
            session_id=payload.session_id,
            citizen_id=payload.citizen_id,
            text=graph_text,
            language=normalized["original_language"],
            original_message=normalized["original_text"],
            extracted_fields=attachment_context["extracted_fields"],
            extracted_text=attachment_context["extracted_text"],
        )
    except Exception as exc:
        logger.error("Graph execution error: %s", repr(exc))
        raise HTTPException(
            status_code=503,
            detail="The AI assistant encountered an error. Please try again shortly.",
        ) from exc

    reply_message = result["messages"][-1]

    try:
        outgoing = await prepare_outgoing(
            reply_text_en=reply_message.content,
            target_language=normalized["original_language"],
            want_audio=False,
        )
    except Exception as exc:
        logger.warning("Translation failed, returning English: %s", repr(exc))
        outgoing = {"text": reply_message.content, "audio_base64": None}

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
    if not payload.audio_base64:
        raise HTTPException(
            status_code=400,
            detail="audio_base64 is required for voice chat.",
        )

    if len(payload.audio_base64) > MAX_ATTACHMENT_B64_LEN:
        raise HTTPException(
            status_code=413,
            detail="Audio recording exceeds maximum allowed size.",
        )

    try:
        attachment_context = await _collect_attachment_context(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Attachment processing error: %s", repr(exc))
        raise HTTPException(
            status_code=422,
            detail="Could not process the attachment.",
        ) from exc

    try:
        normalized = await normalize_incoming(
            text=payload.message,
            audio_base64=payload.audio_base64,
            declared_language=payload.language,
            mime_type=payload.mime_type,
        )
    except ValueError as exc:
        # STT returned empty transcript
        raise HTTPException(
            status_code=422,
            detail=str(exc) or "Could not transcribe the audio. Please try speaking again.",
        ) from exc
    except Exception as exc:
        logger.warning("STT failed: %s", repr(exc))
        raise HTTPException(
            status_code=503,
            detail="Speech recognition is unavailable. Please try text input.",
        ) from exc

    graph_text = _build_graph_text(
        normalized["text"],
        attachment_context["extracted_text"],
        attachment_context["extracted_fields"],
    )

    try:
        result = await _run_graph(
            session_id=payload.session_id,
            citizen_id=payload.citizen_id,
            text=graph_text,
            language=normalized["original_language"],
            original_message=normalized["original_text"],
            extracted_fields=attachment_context["extracted_fields"],
            extracted_text=attachment_context["extracted_text"],
        )
    except Exception as exc:
        logger.error("Graph execution error: %s", repr(exc))
        raise HTTPException(
            status_code=503,
            detail="The AI assistant encountered an error. Please try again.",
        ) from exc

    reply_message = result["messages"][-1]

    try:
        outgoing = await prepare_outgoing(
            reply_text_en=reply_message.content,
            target_language=normalized["original_language"],
            want_audio=True,
        )
    except Exception as exc:
        logger.warning("TTS failed: %s", repr(exc))
        outgoing = {"text": reply_message.content, "audio_base64": None}

    nav_dict = result.get("navigation") or {"action": "none"}

    return ChatResponse(
        session_id=payload.session_id,
        reply_text=outgoing["text"],
        reply_audio_base64=outgoing.get("audio_base64"),
        transcribed_text=normalized["original_text"],
        language=normalized["original_language"],
        intent=result.get("intent"),
        navigation=NavigationAction(**nav_dict),
        tool_calls_made=result.get("tool_calls_made", []),
        sources=_extract_sources(result),
        extracted_fields=attachment_context["extracted_fields"],
    )
