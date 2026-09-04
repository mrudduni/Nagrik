import base64
import requests
from pathlib import Path

audio_path = Path("test_voice.m4a")

audio_base64 = base64.b64encode(audio_path.read_bytes()).decode()

payload = {
    "session_id": "voice-test-1",
    "citizen_id": "test-citizen",
    "message": "",
    "language": None,
    "attachments": [
        {
            "type": "audio",
            "base64_data": audio_base64,
            "mime_type": "audio/mp4"
        }
    ]
}

response = requests.post(
    "http://127.0.0.1:8000/chat/voice",
    json=payload,
    timeout=120
)

print("STATUS:", response.status_code)

if response.status_code == 200:
    data = response.json()

    print("Reply:", data.get("reply_text"))
    print("Language:", data.get("language"))
    print("Intent:", data.get("intent"))
    print("Audio received:", bool(data.get("reply_audio_base64")))

    audio = data.get("reply_audio_base64")
    if audio:
        print("Audio Base64 length:", len(audio))
else:
    print("ERROR:", response.text)