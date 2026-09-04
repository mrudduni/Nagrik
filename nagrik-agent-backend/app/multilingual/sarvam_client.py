"""
Thin wrapper around Sarvam AI's API for Indian-language STT, TTS, and
translation. Kept as a plain client (not a LangChain tool) because it's
used at the graph's I/O edge, not called by the LLM as a reasoning tool.

speech_to_text() now uses the official `sarvamai` SDK internally (already
a pinned dependency, verified by inspecting the installed package
directly rather than guessing) instead of a hand-rolled httpx JSON-body
POST. The previous implementation sent {"audio": <base64>} as a JSON
body, but Sarvam's real STT endpoint expects a multipart/form-data file
upload — that mismatch was the source of the 400 Bad Request. translate()
and text_to_speech() are untouched: they weren't reported as broken and
aren't part of this fix.
"""
import base64
from unittest import result
import httpx
from app.config import settings

from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError


class SarvamUnavailableError(RuntimeError):
    """Raised when Sarvam cannot be used and caller should apply fallback behavior."""


# Sarvam's input_audio_codec accepts a fixed set of literal values (verified
# against the installed sarvamai SDK's transcribe() type signature). This
# maps common audio container magic-byte signatures to those literals, so
# the correct codec can be sent to give the API the ability to decode
# formats that aren't self-evident from just the raw bytes (M4A/MP4 in
# particular, which is what triggered the original bug report).
def _detect_audio_codec(audio_bytes: bytes) -> str | None:
    if len(audio_bytes) < 12:
        return None
    if audio_bytes[0:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "wav"
    if audio_bytes[4:8] == b"ftyp":
        # M4A/MP4 container (ISO base media file format) — this is
        # exactly the case reported: an M4A file with mime_type
        # "audio/mp4" was being sent as a raw JSON base64 string with no
        # codec hint at all.
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
    return None  # Unrecognized: let Sarvam attempt auto-detection rather than guessing wrong.


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
        Returns:
        {
            "transcript": str,
            "detected_language": str
        }
        """

        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as exc:
            raise SarvamUnavailableError(
            f"Invalid base64 audio data: {exc}"
            ) from exc

    # Prefer the MIME type supplied by the client.
    # Fall back to inspecting the audio bytes.
        codec = None

        if mime_type:
            mime_to_codec = {
            "audio/mp4": "mp4",
            "audio/m4a": "mp4",
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/webm": "webm",
        }
            codec = mime_to_codec.get(mime_type.lower())

        if not codec:
            codec = _detect_audio_codec(audio_bytes)

        requested_language = language_code or "unknown"

        try:
            client = self._get_sdk_client()

            kwargs = {
            "file": ("audio", audio_bytes),
            "language_code": requested_language,
            }

            if codec:
                kwargs["input_audio_codec"] = codec

            print("[DEBUG] STT codec:", codec)
            print("[DEBUG] STT language:", requested_language)
            print("[DEBUG] STT audio bytes:", len(audio_bytes))

            result = client.speech_to_text.transcribe(**kwargs)

            print("[DEBUG] STT raw result:", result)
            print("[DEBUG] STT transcript:", result.transcript)
            print("[DEBUG] STT detected language:", result.language_code)

            print("[DEBUG] SARVAM RAW RESULT:", result)
            print("[DEBUG] RESULT TYPE:", type(result))
            print("[DEBUG] TRANSCRIPT VALUE:", getattr(result, "transcript", None))
            print("[DEBUG] LANGUAGE VALUE:", getattr(result, "language_code", None))

            transcript = (result.transcript or "").strip()

            return {
            "transcript": transcript,
            "detected_language": result.language_code or requested_language,
            }

        except ApiError as exc:
            raise SarvamUnavailableError(
            f"Sarvam STT failed ({exc.status_code}): {exc.body}"
            ) from exc

        except SarvamUnavailableError:
            raise

        except Exception as exc:
            raise SarvamUnavailableError(
            f"Sarvam STT failed: {exc}"
            ) from exc
        
    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "ishita",
        ) -> str:
        """Generate speech and return base64-encoded audio."""

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
                    print("[DEBUG] TTS STATUS:", resp.status_code)
                    print("[DEBUG] TTS RESPONSE:", resp.text)

                resp.raise_for_status()

                data = resp.json()

            

                audios = data.get("audios", [])

                if not audios:
                    raise SarvamUnavailableError(
                    "Sarvam TTS returned no audio."
                    )

                return audios[0]

        except (httpx.HTTPError, SarvamUnavailableError) as exc:
            raise SarvamUnavailableError(str(exc)) from exc
        
    async def translate(self, text: str, source_language_code: str,
                         target_language_code: str) -> str:
        """Unchanged."""
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
                resp.raise_for_status()
                data = resp.json()
                return data.get("translated_text", text)
        except (httpx.HTTPError, SarvamUnavailableError) as exc:
            raise SarvamUnavailableError(str(exc)) from exc


sarvam_client = SarvamClient()


def audio_bytes_to_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")