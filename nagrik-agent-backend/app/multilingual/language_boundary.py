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
from app.multilingual.sarvam_client import SarvamUnavailableError
from app.config import settings

PIVOT_LANGUAGE = "en-IN"
ENGLISH_ALIASES = {"en", "en-IN", "en-US", "en-GB"}

HINGLISH_HINTS = {
    "aadhar", "aadhaar", "yojana", "sarkar", "sarkari", "paisa", "paise",
    "kisan", "mahila", "bima", "garib", "gareeb", "kaise", "kya", "hai",
    "hoga", "milega", "chahiye", "shikayat", "pension", "ration",
}


def detect_text_language(text: str | None, declared_language: str | None = None) -> str:
    """
    Lightweight local detection for routing/fallbacks.
    Sarvam remains the source of truth when audio/STT or translation is used.
    """
    if declared_language and declared_language not in ("auto", "detect"):
        return declared_language

    value = text or ""
    if any("\u0900" <= char <= "\u097f" for char in value):
        return "hi-IN"

    words = {word.strip(".,?!:;()[]{}\"'").lower() for word in value.split()}
    if words & HINGLISH_HINTS:
        return "hi-IN"

    return PIVOT_LANGUAGE


async def _translate_or_fallback(
    text: str,
    source_language_code: str,
    target_language_code: str,
) -> str:
    if not text or source_language_code in ENGLISH_ALIASES and target_language_code in ENGLISH_ALIASES:
        return text

    try:
        return await sarvam_client.translate(
            text,
            source_language_code=source_language_code,
            target_language_code=target_language_code,
        )
    except SarvamUnavailableError:
        if settings.enable_sarvam_fallbacks:
            return text
        raise


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
        detected_lang = stt_result.get("detected_language") or declared_language or PIVOT_LANGUAGE
    else:
        transcript = text or ""
        detected_lang = detect_text_language(transcript, declared_language)

    if detected_lang and detected_lang not in ENGLISH_ALIASES:
        pivot_text = await _translate_or_fallback(
            transcript,
            source_language_code=detected_lang,
            target_language_code=PIVOT_LANGUAGE,
        )
    else:
        pivot_text = transcript

    return {
        "text": pivot_text,
        "original_text": transcript,
        "original_language": detected_lang,
    }


async def prepare_outgoing(
    reply_text_en: str,
    target_language: str,
    want_audio: bool,
) -> dict:
    """
    Returns {'text': localized_text, 'audio_base64': str | None}
    """
    if target_language and target_language not in ENGLISH_ALIASES:
        localized_text = await _translate_or_fallback(
            reply_text_en,
            source_language_code=PIVOT_LANGUAGE,
            target_language_code=target_language,
        )
    else:
        localized_text = reply_text_en

    audio_base64 = None
    if want_audio:
        try:
            audio_base64 = await sarvam_client.text_to_speech(
                localized_text, language_code=target_language or PIVOT_LANGUAGE
            )
        except SarvamUnavailableError:
            if not settings.enable_sarvam_fallbacks:
                raise

    return {"text": localized_text, "audio_base64": audio_base64}
