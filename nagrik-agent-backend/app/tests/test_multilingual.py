"""
Multilingual boundary tests. Requires a valid SARVAM_API_KEY to actually
hit the API — mock sarvam_client in CI if you want these to run without
network access.
"""
import pytest
from app.multilingual.language_boundary import (
    detect_text_language,
    normalize_incoming,
    prepare_outgoing,
)


@pytest.mark.asyncio
async def test_normalize_incoming_text_passthrough_for_english():
    result = await normalize_incoming(text="Hello there", audio_base64=None, declared_language="en")
    assert result["text"] == "Hello there"
    assert result["original_language"] == "en"


@pytest.mark.asyncio
async def test_prepare_outgoing_skips_translation_for_english():
    result = await prepare_outgoing(reply_text_en="Hello there", target_language="en", want_audio=False)
    assert result["text"] == "Hello there"
    assert result["audio_base64"] is None


def test_detect_text_language_detects_devanagari_hindi():
    assert detect_text_language("मुझे किसान योजना की जानकारी चाहिए") == "hi-IN"


def test_detect_text_language_detects_hinglish():
    assert detect_text_language("Kisan yojana ka benefit kaise milega?") == "hi-IN"


@pytest.mark.asyncio
async def test_normalize_incoming_uses_translation_for_hindi(monkeypatch):
    async def fake_translate(text, source_language_code, target_language_code):
        assert source_language_code == "hi-IN"
        assert target_language_code == "en-IN"
        return "How do I get a farmer scheme benefit?"

    monkeypatch.setattr(
        "app.multilingual.language_boundary.sarvam_client.translate",
        fake_translate,
    )

    result = await normalize_incoming(
        text="किसान योजना का लाभ कैसे मिलेगा?",
        audio_base64=None,
        declared_language=None,
    )

    assert result["text"] == "How do I get a farmer scheme benefit?"
    assert result["original_language"] == "hi-IN"
