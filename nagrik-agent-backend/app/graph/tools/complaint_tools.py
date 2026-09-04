"""
Self-contained complaint tools for the LangGraph agent.

These tools do NOT require the separate PostgreSQL-backed complaint_service
to be running.  Instead they:
  1. Classify the text using a keyword+rule classifier (same logic as
     backend/complaint_service/app/services/classifier.py, ported here).
  2. Score priority using the same formula as priority_scorer.py.
  3. Persist complaints in an in-memory store (sufficient for a hackathon
     demo; replace with real DB calls once the complaint service is available).
  4. Generate NGR-XXXX reference IDs so citizens get a real tracking number.

When USE_MOCK_BACKENDS=false AND person3_api_base is reachable, the tools
transparently forward to the real complaint service.  Otherwise they run
fully self-contained.

TODO: Replace in-memory store with actual DB persistence once
      backend/complaint_service is configured with a database.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import tool

from app.config import settings


# ---------------------------------------------------------------------------
# In-memory complaint store  (keyed by complaint_id)
# ---------------------------------------------------------------------------
_COMPLAINT_STORE: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Department map  (category -> department name)
# ---------------------------------------------------------------------------
_DEPARTMENT_MAP: dict[str, str] = {
    "POTHOLE":          "Municipal Corporation — Roads & Infrastructure",
    "WATER_SUPPLY":     "Water Supply & Sanitation Department",
    "DRAINAGE":         "Water Supply & Sewerage Board",
    "GARBAGE":          "Sanitation & Waste Management Department",
    "STREETLIGHT":      "Electricity & Street Lighting Department",
    "POLLUTION":        "State Pollution Control Board",
    "NOISE":            "Encroachment & Public Safety Department",
    "ENCROACHMENT":     "Encroachment & Public Safety Department",
    "TRAFFIC":          "Traffic Police / Municipal Traffic Cell",
    "ELECTRICITY":      "Electricity Distribution Company (DISCOM)",
    "PUBLIC_TRANSPORT": "Urban Transport / State Road Transport",
    "SANITATION":       "Urban Local Body — Sanitation Wing",
    "OTHER":            "General Grievance Cell — Municipal Corporation",
}

_SLA_HOURS_MAP: dict[str, int] = {
    "CRITICAL": 24,
    "HIGH":     48,
    "MEDIUM":   72,
    "LOW":      120,
}


# ---------------------------------------------------------------------------
# Inline keyword classifier
# ---------------------------------------------------------------------------
def _classify_by_keywords(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["pothole", "gadda", "road", "crater", "asphalt", "tar"]):
        return "POTHOLE"
    if any(w in t for w in ["water", "paani", "tap", "pipeline", "leak", "supply"]):
        return "WATER_SUPPLY"
    if any(w in t for w in ["drain", "nala", "sewage", "gutter", "waterlogging", "overflow"]):
        return "DRAINAGE"
    if any(w in t for w in ["garbage", "kachra", "trash", "dustbin", "waste", "litter"]):
        return "GARBAGE"
    if any(w in t for w in ["light", "streetlight", "bulb", "dark", "pole", "lamp"]):
        return "STREETLIGHT"
    if any(w in t for w in ["smoke", "pollution", "smog", "toxic", "air quality"]):
        return "POLLUTION"
    if any(w in t for w in ["noise", "loudspeaker", "music", "dj", "construction hours"]):
        return "NOISE"
    if any(w in t for w in ["encroach", "illegal", "footpath", "stall", "hawker", "vendor"]):
        return "ENCROACHMENT"
    if any(w in t for w in ["traffic", "jam", "signal", "congestion"]):
        return "TRAFFIC"
    if any(w in t for w in ["power", "electricity", "transformer", "bijli", "voltage", "wire"]):
        return "ELECTRICITY"
    if any(w in t for w in ["bus", "transport", "auto", "rickshaw", "metro"]):
        return "PUBLIC_TRANSPORT"
    if any(w in t for w in ["toilet", "sanitation", "cleaning", "washroom", "latrine"]):
        return "SANITATION"
    return "OTHER"


def _get_severity(text: str, category: str) -> int:
    t = text.lower()
    if any(w in t for w in [
        "urgent", "emergency", "fatal", "dangerous", "collapse",
        "fire", "flood", "electrocution", "accident", "death",
    ]):
        return 5
    if any(w in t for w in [
        "severe", "major", "completely", "blocking", "days",
        "weeks", "attack", "fallen", "injured",
    ]):
        return 4
    if any(w in t for w in [
        "many", "daily", "frequently", "smells", "unsafe", "broken",
    ]):
        return 3
    if category in ("WATER_SUPPLY", "ELECTRICITY", "DRAINAGE"):
        return 3
    return 2


def _priority_tier(severity: int) -> str:
    score = severity * 15  # base score (no cluster/age for new complaints)
    if score >= 75:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def _generate_complaint_id() -> str:
    suffix = uuid.uuid4().hex[:6].upper()
    return f"NGR-{suffix}"


def _human_category(category: str) -> str:
    return category.replace("_", " ").title()


# ---------------------------------------------------------------------------
# LangChain tools
# ---------------------------------------------------------------------------

@tool
async def file_complaint(
    citizen_id: str,
    text: str,
    location: Optional[str] = None,
) -> dict:
    """
    File a civic grievance / complaint on behalf of a citizen.

    Args:
        citizen_id: The citizen's ID from the session.
        text: The full complaint description in the citizen's words.
        location: Optional location or address string.

    Returns a dict with complaint_id, category, priority_tier, department,
    sla_hours, and status.  The complaint_id (NGR-XXXXXX format) can be
    used later with check_complaint_status.
    """
    # --- Try real complaint service first ---
    if not settings.use_mock_backends:
        try:
            from app.integrations.person3_client import person3_client
            result = await person3_client.file_complaint(
                citizen_id=citizen_id,
                text=text,
                location={"address": location} if location else {},
            )
            return result
        except Exception:
            pass  # fall through to self-contained implementation

    # --- Self-contained classification ---
    category = _classify_by_keywords(text)
    severity = _get_severity(text, category)
    tier = _priority_tier(severity)
    department = _DEPARTMENT_MAP.get(category, _DEPARTMENT_MAP["OTHER"])
    sla_hours = _SLA_HOURS_MAP[tier]
    complaint_id = _generate_complaint_id()

    record = {
        "complaint_id": complaint_id,
        "citizen_id": citizen_id,
        "text": text,
        "location": location or "Not specified",
        "category": category,
        "category_label": _human_category(category),
        "severity": severity,
        "priority_tier": tier,
        "department": department,
        "sla_hours": sla_hours,
        "status": "SUBMITTED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _COMPLAINT_STORE[complaint_id] = record

    return {
        "complaint_id": complaint_id,
        "category": _human_category(category),
        "priority": tier,
        "department": department,
        "sla_hours": sla_hours,
        "status": "Submitted",
        "message": (
            f"Complaint registered successfully.\n"
            f"Complaint ID: {complaint_id}\n"
            f"Category: {_human_category(category)}\n"
            f"Priority: {tier}\n"
            f"Department: {department}\n"
            f"Expected resolution within {sla_hours} hours."
        ),
    }


@tool
async def check_complaint_status(complaint_id: str) -> dict:
    """
    Check the current status and details of a previously filed complaint.

    Args:
        complaint_id: The NGR-XXXXXX reference number given when the
                      complaint was filed.

    Returns a dict with status, department, category, and timeline info.
    """
    # --- Try real complaint service first ---
    if not settings.use_mock_backends:
        try:
            from app.integrations.person3_client import person3_client
            return await person3_client.check_status(complaint_id)
        except Exception:
            pass

    # --- In-memory lookup ---
    cid = complaint_id.strip().upper()
    # Normalize: user may say "NGR-ABC123" or just "NGRABC123"
    if not cid.startswith("NGR-"):
        # Try to find a fuzzy match
        match = next(
            (k for k in _COMPLAINT_STORE if k.replace("-", "").endswith(cid.replace("-", ""))),
            None,
        )
        if match:
            cid = match

    record = _COMPLAINT_STORE.get(cid)
    if not record:
        return {
            "found": False,
            "complaint_id": complaint_id,
            "message": (
                f"No complaint found with ID {complaint_id}. "
                "Please check the reference number and try again."
            ),
        }

    # Simulate progression: complaints > 1 hour old are "ACKNOWLEDGED"
    created = datetime.fromisoformat(record["created_at"])
    now = datetime.now(timezone.utc)
    age_minutes = (now - created).total_seconds() / 60

    if age_minutes > 60:
        status = "ACKNOWLEDGED"
    elif age_minutes > 5:
        status = "SUBMITTED"
    else:
        status = "SUBMITTED"

    return {
        "found": True,
        "complaint_id": record["complaint_id"],
        "category": record.get("category_label", record["category"]),
        "priority": record["priority_tier"],
        "department": record["department"],
        "status": status,
        "location": record.get("location", "Not specified"),
        "submitted_at": record["created_at"],
        "sla_hours": record["sla_hours"],
        "message": (
            f"Complaint {record['complaint_id']}: {status}\n"
            f"Category: {record.get('category_label', record['category'])}\n"
            f"Department: {record['department']}\n"
            f"Priority: {record['priority_tier']}\n"
            f"Expected resolution within {record['sla_hours']} hours of submission."
        ),
    }


COMPLAINT_TOOLS = [file_complaint, check_complaint_status]
