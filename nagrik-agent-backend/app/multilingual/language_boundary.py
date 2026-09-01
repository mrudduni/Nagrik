"""
Graph-edge language handling. This is deliberately OUTSIDE the core
LangGraph reasoning graph: incoming audio/non-English text is normalized
to a pivot language (English) before it ever reaches intent
detection/tools/RAG, and the final reply is translated + spoken back out
afterward. This keeps the entire core graph language-agnostic, so no
node/tool needs to know or care what language the citizen used.

Flow:
  audio_in  -> STT (Sarvam) -> [translate to English if needed] -> graph
  graph_out -> [translate to citizen's language if needed] -> TTS (Sarvam) -> audio_out
"""
from app.multilingual.sarvam_client import sarvam_client

PIVOT_LANGUAGE = "en-IN"


async def normalize_incoming(
    text: str | None,
    audio_base64: str | None,
    declared_language: str | None,
) -> dict:
    """
    Returns {'text': str_in_pivot_language, 'original_language': str}
    Handles: text-in-Indian-language, audio-in, or plain English text.
    """
    if audio_base64:
        stt_result = await sarvam_client.speech_to_text(audio_base64, language_code=declared_language)
        transcript = stt_result["transcript"]
        detected_lang = stt_result["detected_language"]
    else:
        transcript = text or ""
        detected_lang = declared_language or "en-IN"

    if detected_lang and detected_lang not in (PIVOT_LANGUAGE, "en"):
        pivot_text = await sarvam_client.translate(
            transcript, source_language_code=detected_lang, target_language_code=PIVOT_LANGUAGE
        )
    else:
        pivot_text = transcript

    return {"text": pivot_text, "original_language": detected_lang}


async def prepare_outgoing(
    reply_text_en: str,
    target_language: str,
    want_audio: bool,
) -> dict:
    """
    Returns {'text': localized_text, 'audio_base64': str | None}
    """
    if target_language and target_language not in (PIVOT_LANGUAGE, "en"):
        localized_text = await sarvam_client.translate(
            reply_text_en, source_language_code=PIVOT_LANGUAGE, target_language_code=target_language
        )
    else:
        localized_text = reply_text_en

    audio_base64 = None
    if want_audio:
        audio_base64 = await sarvam_client.text_to_speech(
            localized_text, language_code=target_language or PIVOT_LANGUAGE
        )

    return {"text": localized_text, "audio_base64": audio_base64}
