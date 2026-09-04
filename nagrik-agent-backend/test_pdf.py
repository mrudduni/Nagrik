import base64
import requests
from pathlib import Path

pdf_path = Path("data/text_data/Namo Shetkari Mahasanman Nidhi Yojana.pdf")

pdf_base64 = base64.b64encode(pdf_path.read_bytes()).decode()

payload = {
    "session_id": "pdf-test-1",
    "citizen_id": "test-citizen",
    "message": "What scheme is this document about and what are its benefits?",
    "language": "en",
    "attachments": [
        {
            "type": "document",
            "base64_data": pdf_base64,
            "mime_type": "application/pdf"
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