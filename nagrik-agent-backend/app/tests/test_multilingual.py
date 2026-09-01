"""
Multilingual boundary tests. Requires a valid SARVAM_API_KEY to actually
hit the API — mock sarvam_client in CI if you want these to run without
network access.
"""
import pytest
from app.multilingual.language_boundary import normalize_incoming, prepare_outgoing


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
