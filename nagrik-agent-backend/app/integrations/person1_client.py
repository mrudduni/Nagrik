"""
HTTP client for Person 1's Citizen & Scheme backend.

While Person 1's real API isn't ready, USE_MOCK_BACKENDS=true returns
canned data matching the agreed contract, so graph/tool logic can be
built and tested against a stable shape from day one. Flip the env var
(no code change needed here) once the real API is live.
"""
import httpx
from app.config import settings

_MOCK_SCHEMES = [
    {
        "id": "sch_001",
        "name": "Post-Matric Scholarship for SC/ST Students",
        "ministry": "Ministry of Social Justice and Empowerment",
        "department": "Department of Social Justice",
        "summary": "Financial assistance for SC/ST students pursuing post-matriculation studies.",
    },
    {
        "id": "sch_002",
        "name": "PM Vishwakarma Scheme",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "department": "MSME",
        "summary": "Support for traditional artisans and craftspeople, including skill training and credit.",
    },
]


class Person1Client:
    def __init__(self):
        self.base_url = settings.person1_api_base
        self.mock = settings.use_mock_backends

    async def get_schemes(self, citizen_id: str) -> list[dict]:
        if self.mock:
            return _MOCK_SCHEMES
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/schemes", params={"citizen_id": citizen_id})
            resp.raise_for_status()
            return resp.json()

    async def check_eligibility(self, scheme_id: str, citizen_id: str) -> dict:
        if self.mock:
            return {"eligible": "possible", "reasons": ["Income and category checks require citizen profile confirmation."]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/schemes/{scheme_id}/eligibility",
                params={"citizen_id": citizen_id},
            )
            resp.raise_for_status()
            return resp.json()

    async def compare_schemes(self, scheme_ids: list[str]) -> dict:
        if self.mock:
            return {
                "schemes": [s for s in _MOCK_SCHEMES if s["id"] in scheme_ids],
                "comparison_note": "Mock comparison — replace once Person 1's real endpoint is live.",
            }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/schemes/compare", params={"ids": scheme_ids})
            resp.raise_for_status()
            return resp.json()

    async def get_profile(self, citizen_id: str) -> dict:
        if self.mock:
            return {"citizen_id": citizen_id, "name": None, "known_fields": {}}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/citizen/{citizen_id}/profile")
            resp.raise_for_status()
            return resp.json()


person1_client = Person1Client()
