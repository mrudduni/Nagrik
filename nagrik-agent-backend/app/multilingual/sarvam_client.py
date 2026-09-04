"""
Thin wrapper around Sarvam AI's API for Indian-language STT, TTS, and
translation, with multi-tier fallback to OpenAI Whisper and Gemini Multimodal STT
when Sarvam is unavailable or unconfigured.
"""
import base64
import httpx
from app.config import settings

try:
    from sarvamai import SarvamAI
    from sarvamai.core.api_error import ApiError
except ImportError:
    SarvamAI = None
    class ApiError(Exception):
        pass


class SarvamUnavailableError(RuntimeError):
    """Raised when Sarvam cannot be used and caller should apply fallback behavior."""


def _detect_audio_codec(audio_bytes: bytes) -> str | None:
    if len(audio_bytes) < 12:
        return None
    if audio_bytes[0:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "wav"
    if audio_bytes[4:8] == b"ftyp":
        return "mp4"
    if audio_bytes[0:3] == b"ID3" or audio_bytes[0:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if audio_bytes[0:4] == b"OggS":
        return "ogg"
    if audio_bytes[0:4] == b"fLaC":
        return "flac"
    if audio_bytes[0:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if audio_bytes[0:4] == b"FORM" and audio_bytes[8:12] == b"AIFF":
        return "aiff"
    return None


async def _whisper_speech_to_text(audio_bytes: bytes, mime_type: str | None, language_code: str | None) -> dict:
    key = settings.openai_api_key
    if not key or "placeholder" in key.lower() or key.startswith("your_"):
        raise SarvamUnavailableError("OpenAI API key unavailable for Whisper STT.")
    
    import io
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=key)
    
    ext = "webm"
    if mime_type:
        mime = mime_type.lower()
        if "wav" in mime:
            ext = "wav"
        elif "mp4" in mime or "m4a" in mime:
            ext = "m4a"
        elif "mp3" in mime or "mpeg" in mime:
            ext = "mp3"
        elif "ogg" in mime:
            ext = "ogg"

    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = f"recording.{ext}"

    kwargs = {"model": "whisper-1", "file": file_obj}
    if language_code and language_code not in ("auto", "detect", "unknown"):
        kwargs["language"] = language_code.split("-")[0]

    resp = await client.audio.transcriptions.create(**kwargs)
    transcript = (resp.text or "").strip()
    return {
        "transcript": transcript,
        "detected_language": language_code or "en-IN",
    }


async def _gemini_speech_to_text(audio_bytes: bytes, mime_type: str | None, language_code: str | None) -> dict:
    key = settings.gemini_api_key
    if not key or "placeholder" in key.lower() or key.startswith("your_"):
        raise SarvamUnavailableError("Gemini API key unavailable for STT.")
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    actual_mime = mime_type or "audio/webm"
    if ";" in actual_mime:
        actual_mime = actual_mime.split(";")[0]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=key,
        temperature=0,
    )
    prompt = (
        "Accurately transcribe the spoken audio recording into text. "
        "Return ONLY the verbatim spoken text transcript. "
        "Do not add any preamble, commentary, or formatting. If silent, return an empty string."
    )
    msg = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "media", "mime_type": actual_mime, "data": b64_audio},
        ]
    )
    res = await llm.ainvoke([msg])
    transcript = (res.content or "").strip()
    return {
        "transcript": transcript,
        "detected_language": language_code or "en-IN",
    }


class SarvamClient:
    def __init__(self):
        self.base_url = settings.sarvam_base_url
        self.api_key = settings.sarvam_api_key
        self._sdk_client: SarvamAI | None = None

    def _headers(self) -> dict:
        if not self.api_key:
            raise SarvamUnavailableError("SARVAM_API_KEY is not configured.")
        return {"api-subscription-key": self.api_key}

    def _get_sdk_client(self) -> SarvamAI:
        if not self.api_key:
            raise SarvamUnavailableError("SARVAM_API_KEY is not configured.")
        if self._sdk_client is None:
            self._sdk_client = SarvamAI(api_subscription_key=self.api_key)
        return self._sdk_client

    async def speech_to_text(
        self,
        audio_base64: str,
        language_code: str | None = None,
        mime_type: str | None = None,
    ) -> dict:
        """
        Transcribe audio to text using Sarvam AI, with automatic fallback
        to OpenAI Whisper and Gemini Multimodal STT.
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as exc:
            raise SarvamUnavailableError(f"Invalid base64 audio data: {exc}") from exc

        # 1. Try Sarvam AI STT if API key is present
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                mime_to_codec = {
                    "audio/mp4": "mp4",
                    "audio/m4a": "mp4",
                    "audio/wav": "wav",
                    "audio/x-wav": "wav",
                    "audio/mpeg": "mp3",
                    "audio/mp3": "mp3",
                    "audio/webm": "webm",
                }
                codec = mime_to_codec.get(mime_type.lower()) if mime_type else None
                if not codec:
                    codec = _detect_audio_codec(audio_bytes)

                requested_language = language_code or "unknown"
                client = self._get_sdk_client()
                kwargs = {
                    "file": ("audio", audio_bytes),
                    "language_code": requested_language,
                }
                if codec:
                    kwargs["input_audio_codec"] = codec

                result = client.speech_to_text.transcribe(**kwargs)
                transcript = (getattr(result, "transcript", "") or "").strip()

                if transcript:
                    return {
                        "transcript": transcript,
                        "detected_language": getattr(result, "language_code", None) or requested_language,
                    }
            except Exception as exc:
                print(f"[STT] Sarvam STT failed: {exc}. Trying OpenAI Whisper fallback...")

        # 2. Fallback to OpenAI Whisper STT
        try:
            return await _whisper_speech_to_text(audio_bytes, mime_type, language_code)
        except Exception as exc1:
            print(f"[STT] OpenAI Whisper fallback failed: {exc1}. Trying Gemini STT fallback...")

        # 3. Fallback to Gemini Multimodal STT
        try:
            return await _gemini_speech_to_text(audio_bytes, mime_type, language_code)
        except Exception as exc2:
            raise SarvamUnavailableError(
                f"All STT providers failed (Sarvam, Whisper, Gemini): {exc2}"
            ) from exc2

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "ishita",
    ) -> str | None:
        """Generate speech and return base64-encoded audio. Graceful fallback on error."""
        if not self.api_key or self.api_key.startswith("your_"):
            return None

        payload = {
            "text": text,
            "model": "bulbul:v3",
            "language_code": language_code,
            "speaker": speaker,
            "output_audio_codec": "wav",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code >= 400:
                    return None
                data = resp.json()
                audios = data.get("audios", [])
                return audios[0] if audios else None
        except Exception:
            return None

    async def translate(
        self,
        text: str,
        source_language_code: str,
        target_language_code: str,
    ) -> str:
        """Translate text with graceful fallback."""
        if not self.api_key or self.api_key.startswith("your_"):
            return text

        payload = {
            "input": text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/translate",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code >= 400:
                    return text
                data = resp.json()
                return data.get("translated_text", text)
        except Exception:
            return text


sarvam_client = SarvamClient()


def audio_bytes_to_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")