"""
Optional Twilio integration for actual phone calls. Deliberately thin:
all real STT/TTS logic lives in multilingual/sarvam_client.py so it isn't
duplicated between the web /chat/voice path and phone calls.

This is a stub to fill in if time allows (Day 11-13 buffer) — wire up
Twilio's <Gather>/<Record> webhooks to fetch audio, call
multilingual.language_boundary, and respond with TwiML pointing at the
resulting TTS audio.
"""
from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/voice/twilio/incoming")
async def twilio_incoming(request: Request):
    # TODO (if time allows): parse Twilio's form-encoded webhook payload,
    # extract RecordingUrl, download audio, run through
    # multilingual.language_boundary.normalize_incoming(), invoke the
    # graph, then prepare_outgoing() and return TwiML <Play> pointing at
    # the resulting audio.
    return {"status": "not_implemented", "note": "Wire up if time allows after core demo is stable."}
