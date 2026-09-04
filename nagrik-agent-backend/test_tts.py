import asyncio
import base64

from app.multilingual.sarvam_client import sarvam_client


async def main():
    text = "Hello, this is a test of the Nagrik voice assistant."

    audio_base64 = await sarvam_client.text_to_speech(
        text=text,
        language_code="en-IN",
        speaker="ishita",
    )

    # DO NOT print the Base64 audio itself
    print("TTS result received")
    print("Result type:", type(audio_base64).__name__)
    print("Audio received:", bool(audio_base64))
    print("Base64 length:", len(audio_base64) if audio_base64 else 0)

    if not audio_base64:
        print("FAILED: No audio returned")
        return

    try:
        audio_bytes = base64.b64decode(audio_base64)

        with open("tts_test.wav", "wb") as f:
            f.write(audio_bytes)

        print("SUCCESS")
        print("Audio bytes:", len(audio_bytes))
        print("Saved: tts_test.wav")

    except Exception as e:
        print("FAILED while decoding audio:", e)


if __name__ == "__main__":
    asyncio.run(main())