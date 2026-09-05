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


def detect_text_language(
    text: str | None,
    declared_language: str | None = None,
) -> str:
    """
    Detect the language of text locally using Unicode script ranges.

    An explicitly declared language always takes priority.
    Otherwise detect Indian scripts and use simple scoring
    for Romanized Indian-language text.
    """

    if declared_language and declared_language not in ("auto", "detect"):
        return declared_language

    value = (text or "").strip()

    if not value:
        return PIVOT_LANGUAGE

    # ---------------------------------------------------------
    # Indian scripts
    # ---------------------------------------------------------

    # Hindi / Marathi / Nepali / Sanskrit
    if any("\u0900" <= char <= "\u097F" for char in value):
        return "hi-IN"

    # Bengali / Assamese
    if any("\u0980" <= char <= "\u09FF" for char in value):
        return "bn-IN"

    # Gujarati
    if any("\u0A80" <= char <= "\u0AFF" for char in value):
        return "gu-IN"

    # Punjabi / Gurmukhi
    if any("\u0A00" <= char <= "\u0A7F" for char in value):
        return "pa-IN"

    # Tamil
    if any("\u0B80" <= char <= "\u0BFF" for char in value):
        return "ta-IN"

    # Telugu
    if any("\u0C00" <= char <= "\u0C7F" for char in value):
        return "te-IN"

    # Kannada
    if any("\u0C80" <= char <= "\u0CFF" for char in value):
        return "kn-IN"

    # Malayalam
    if any("\u0D00" <= char <= "\u0D7F" for char in value):
        return "ml-IN"

    # ---------------------------------------------------------
    # Romanized Indian language detection
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # Do NOT classify a message as Hindi just because it
    # contains words such as "yojana", "bima", "kisan", etc.
    #
    # Government scheme names are often Indian words even when
    # the user's actual question is English.
    #
    # Only classify as Hinglish when there are multiple
    # conversational Hindi indicators.
    # ---------------------------------------------------------

    words = {
        word.strip(".,?!:;()[]{}\"'").lower()
        for word in value.split()
    }

    hinglish_conversation_hints = {
        "kya",
        "kaise",
        "kaisa",
        "kaisi",
        "kyun",
        "kyu",
        "kab",
        "kahan",
        "kahaan",
        "hai",
        "hain",
        "hoga",
        "hogi",
        "honge",
        "milega",
        "milega",
        "milta",
        "milti",
        "chahiye",
        "batao",
        "bataye",
        "bataiye",
        "samjhao",
        "samjha",
        "mujhe",
        "mera",
        "meri",
        "mere",
        "aap",
        "apka",
        "apki",
        "ke",
        "ko",
        "se",
        "mein",
        "me",
        "par",
        "wala",
        "wali",
        "liye",
        "nahi",
        "nahin",
        "kr",
        "karna",
        "karo",
        "do",
        "dijiye",
    }

    hint_count = len(words & hinglish_conversation_hints)

    # Require at least 2 conversational Hindi indicators.
    if hint_count >= 2:
        return "hi-IN"

    # Otherwise treat Roman/Latin text as English.
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
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Sarvam translate failed/exhausted (%s), using raw text fallback", repr(exc))
        return text


async def _transcribe_with_gemini(
    audio_base64: str,
    mime_type: str | None = None,
    declared_language: str | None = None,
) -> dict:
    """Fallback multimodal STT using Gemini when Sarvam is unavailable."""
    import base64
    import logging
    from google import genai
    from google.genai import types

    logger = logging.getLogger(__name__)

    if not settings.gemini_api_key:
        raise ValueError("No speech recognition service or API key is available.")

    audio_bytes = base64.b64decode(audio_base64)
    clean_mime = (mime_type or "audio/webm").split(";")[0].strip().lower()
    if not clean_mime.startswith("audio/"):
        clean_mime = "audio/webm"

    logger.info("Transcribing audio via Gemini multimodal API (mime: %s, bytes: %d)", clean_mime, len(audio_bytes))

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = (
        "You are an Indian civic governance speech recognition engine. "
        "Listen to this audio recording of a citizen speaking. "
        "Transcribe exactly what they say verbatim in the original spoken language "
        "(e.g., Hindi, English, Hinglish, Bengali, Tamil, Telugu, Marathi, Kannada, etc.). "
        "If there is speech, return ONLY the exact transcript text. "
        "Do NOT translate, do NOT summarize, and do NOT add any quotation marks, explanations, or metadata. "
        "If the audio has no speech (only silence or static), output: SILENCE"
    )
    if declared_language and declared_language not in ("auto", "unknown", "detect"):
        prompt += f" Citizen preferred language: {declared_language}."

    response = client.models.generate_content(
        model=settings.llm_model,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=clean_mime),
            prompt,
        ],
    )
    text = (response.text or "").strip()
    if not text or text.upper() == "SILENCE":
        raise ValueError("Could not detect any speech in the recording. Please try speaking again.")

    detected_lang = detect_text_language(text, declared_language)
    return {
        "transcript": text,
        "detected_language": detected_lang,
    }


async def normalize_incoming(
    text: str | None,
    audio_base64: str | None,
    declared_language: str | None,
    mime_type: str | None = None,
) -> dict:
    """
    Returns:
        {
            "text": str_in_pivot_language,
            "original_text": str,
            "original_language": str
        }

    Handles:
    - text input
    - Indian-language text
    - audio input (Sarvam with automatic Gemini multimodal fallback)
    - automatic language detection
    """

    # ---------------------------------------------------------
    # 1. Get the original text
    # ---------------------------------------------------------
    if audio_base64:
        stt_result = None
        if settings.sarvam_api_key:
            try:
                stt_result = await sarvam_client.speech_to_text(
                    audio_base64,
                    language_code=declared_language,
                    mime_type=mime_type,
                )
            except Exception as sarvam_err:
                import logging
                logging.getLogger(__name__).warning(
                    "Sarvam STT failed (%s), falling back to Gemini multimodal audio...",
                    repr(sarvam_err),
                )

        if not stt_result or not stt_result.get("transcript"):
            stt_result = await _transcribe_with_gemini(
                audio_base64=audio_base64,
                mime_type=mime_type,
                declared_language=declared_language,
            )

        transcript = (stt_result.get("transcript") or "").strip()

        if not transcript:
            raise ValueError("Speech-to-text returned an empty transcript.")

        detected_language = (
            stt_result.get("detected_language")
            or declared_language
            or PIVOT_LANGUAGE
        )

        original_text = transcript
        original_language = detected_language

    else:
        original_text = (text or "").strip()

        if not original_text:
            original_text = "(citizen sent an attachment with no text)"

        original_language = detect_text_language(
            original_text,
            declared_language,
        )

    # ---------------------------------------------------------
    # 2. Normalize language for translation
    # ---------------------------------------------------------
    translation_source_language = original_language

    if translation_source_language == "unknown":
        translation_source_language = "auto"

    # ---------------------------------------------------------
    # 3. Translate to English pivot if necessary
    # ---------------------------------------------------------
    if original_language in ENGLISH_ALIASES:
        pivot_text = original_text
    else:
        pivot_text = await _translate_or_fallback(
            original_text,
            source_language_code=translation_source_language,
            target_language_code=PIVOT_LANGUAGE,
        )

    # ---------------------------------------------------------
    # 4. Debug
    # ---------------------------------------------------------
    print("NORMALIZED TEXT:", pivot_text)
    print("ORIGINAL LANGUAGE:", original_language)

    # ---------------------------------------------------------
    # 5. Return normalized result
    # ---------------------------------------------------------
    return {
        "text": pivot_text,
        "original_text": original_text,
        "original_language": original_language,
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
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Sarvam TTS failed or exhausted (%s), falling back to browser speech synthesis", repr(exc))
            audio_base64 = None

    return {"text": localized_text, "audio_base64": audio_base64}
