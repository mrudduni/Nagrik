"""
Thin wrapper around Sarvam AI's API for Indian-language STT, TTS, and
translation. Kept as a plain client (not a LangChain tool) because it's
used at the graph's I/O edge, not called by the LLM as a reasoning tool.

NOTE: endpoint paths below follow Sarvam's documented REST API shape as
of this build; verify against current Sarvam docs before the demo in
case of versioning changes.
"""
import base64
import httpx
from app.config import settings


class SarvamUnavailableError(RuntimeError):
    """Raised when Sarvam cannot be used and caller should apply fallback behavior."""


class SarvamClient:
    def __init__(self):
        self.base_url = settings.sarvam_base_url
        self.api_key = settings.sarvam_api_key

    def _headers(self) -> dict:
        if not self.api_key:
            raise SarvamUnavailableError("SARVAM_API_KEY is not configured.")
        return {"api-subscription-key": self.api_key}

    async def speech_to_text(self, audio_base64: str, language_code: str | None = None) -> dict:
        """Returns {'transcript': str, 'detected_language': str}."""
        payload = {"audio": audio_base64}
        if language_code:
            payload["language_code"] = language_code
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    f"{self.base_url}/speech-to-text",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "transcript": data.get("transcript", ""),
                    "detected_language": data.get("language_code", language_code or "en-IN"),
                }
        except (httpx.HTTPError, SarvamUnavailableError) as exc:
            raise SarvamUnavailableError(str(exc)) from exc

    async def text_to_speech(self, text: str, language_code: str = "hi-IN",
                              speaker: str = "meera") -> str:
        """Returns base64-encoded audio."""
        payload = {"text": text, "target_language_code": language_code, "speaker": speaker}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("audio", "")
        except (httpx.HTTPError, SarvamUnavailableError) as exc:
            raise SarvamUnavailableError(str(exc)) from exc

    async def translate(self, text: str, source_language_code: str,
                         target_language_code: str) -> str:
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
