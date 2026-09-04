import base64
import requests
from pathlib import Path

image_path = Path("test_image.jpg")

image_base64 = base64.b64encode(image_path.read_bytes()).decode()

payload = {
    "session_id": "image-test-1",
    "citizen_id": "test-citizen",
    "message": "Read this document and tell me what information it contains.",
    "language": "en",
    "attachments": [
        {
            "type": "image",
            "base64_data": image_base64,
            "mime_type": "image/jpeg"
        }
    ]
}

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json=payload,
    timeout=120
)

print("STATUS:", response.status_code)
print(response.text)