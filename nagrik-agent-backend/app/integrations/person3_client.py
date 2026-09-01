"""
HTTP client for Person 3's Complaint & Grievance backend.

Ownership note (agreed in the design doc): this agent extracts raw
structured fields (text, location, media refs) from the conversation;
Person 3's backend owns classification, routing, and severity — we do
NOT duplicate classification logic here.
"""
import uuid
import httpx
from app.config import settings


class Person3Client:
    def __init__(self):
        self.base_url = settings.person3_api_base
        self.mock = settings.use_mock_backends

    async def file_complaint(self, citizen_id: str, text: str, location: dict | None = None,
                              media_refs: list[str] | None = None) -> dict:
        payload = {
            "citizen_id": citizen_id,
            "text": text,
            "location": location or {},
            "media_refs": media_refs or [],
        }
        if self.mock:
            return {
                "complaint_id": f"cmp_{uuid.uuid4().hex[:8]}",
                "department": "Unassigned (mock — Person 3 backend will classify)",
                "status": "received",
            }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self.base_url}/complaints", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def check_status(self, complaint_id: str) -> dict:
        if self.mock:
            return {"complaint_id": complaint_id, "status": "in_progress", "department": "Mock Dept"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/complaints/{complaint_id}/status")
            resp.raise_for_status()
            return resp.json()


person3_client = Person3Client()
