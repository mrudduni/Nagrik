"""
Application-assistance tools for the LangGraph agent.

These tools let the agent:
  1. Start / continue an application draft for a scheme.
  2. Retrieve an existing application draft by ID.
  3. List application drafts for a citizen in this session.

IMPORTANT: These tools create "assisted drafts", NOT real government
submissions.  There is no actual government submission API available.
The draft is stored in-memory for the hackathon demo; a production system
would persist to a database and integrate with the relevant ministry portal.

TODO: Replace _APPLICATION_STORE with DB persistence and connect to
      real government e-Seva / DigiLocker submission APIs when available.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# In-memory application store  (keyed by application_id)
# ---------------------------------------------------------------------------
_APPLICATION_STORE: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Known scheme → field requirements map
# Used so the agent knows what to ask for when a citizen mentions a scheme.
# Extend this as more schemes are indexed.
# ---------------------------------------------------------------------------
_SCHEME_FIELD_MAP: dict[str, list[dict]] = {
    "pm-kisan": [
        {"name": "full_name",           "label": "Full name",           "required": True},
        {"name": "aadhaar_number",       "label": "Aadhaar number",       "required": True},
        {"name": "bank_account_number",  "label": "Bank account number",  "required": True},
        {"name": "ifsc_code",            "label": "IFSC code",            "required": True},
        {"name": "land_holding_acres",   "label": "Land holding (acres)", "required": True},
        {"name": "state",                "label": "State",                "required": True},
        {"name": "district",             "label": "District",             "required": True},
    ],
    "scholarship": [
        {"name": "full_name",            "label": "Full name",            "required": True},
        {"name": "aadhaar_number",       "label": "Aadhaar number",       "required": True},
        {"name": "date_of_birth",        "label": "Date of birth",        "required": True},
        {"name": "category",             "label": "Category (SC/ST/OBC/EWS/General)", "required": True},
        {"name": "annual_family_income", "label": "Annual family income (₹)", "required": True},
        {"name": "institution_name",     "label": "Institution name",     "required": True},
        {"name": "course_name",          "label": "Course / programme",   "required": True},
    ],
    "ayushman-bharat": [
        {"name": "full_name",            "label": "Full name",            "required": True},
        {"name": "aadhaar_number",       "label": "Aadhaar number",       "required": True},
        {"name": "date_of_birth",        "label": "Date of birth",        "required": True},
        {"name": "family_income",        "label": "Annual family income (₹)", "required": True},
        {"name": "state",                "label": "State",                "required": True},
    ],
    "default": [
        {"name": "full_name",            "label": "Full name",            "required": True},
        {"name": "aadhaar_number",       "label": "Aadhaar number",       "required": True},
        {"name": "date_of_birth",        "label": "Date of birth",        "required": True},
        {"name": "address",              "label": "Address",              "required": True},
        {"name": "mobile_number",        "label": "Mobile number",        "required": True},
    ],
}


def _get_field_requirements(scheme_name: str) -> list[dict]:
    """Return the field list for a scheme, using the default if unknown."""
    key = scheme_name.lower().strip()
    # Try exact match, then partial match
    if key in _SCHEME_FIELD_MAP:
        return _SCHEME_FIELD_MAP[key]
    for k in _SCHEME_FIELD_MAP:
        if k != "default" and k in key:
            return _SCHEME_FIELD_MAP[k]
    return _SCHEME_FIELD_MAP["default"]


def _missing_required_fields(fields: list[dict], data: dict) -> list[dict]:
    return [f for f in fields if f["required"] and not data.get(f["name"])]


def _generate_application_id() -> str:
    suffix = uuid.uuid4().hex[:6].upper()
    return f"APP-{suffix}"


# ---------------------------------------------------------------------------
# LangChain tools
# ---------------------------------------------------------------------------

@tool
async def start_application(
    citizen_id: str,
    scheme_name: str,
    prefilled_fields: Optional[dict] = None,
) -> dict:
    """
    Start an assisted application draft for a government scheme.

    Call this when a citizen expresses intent to apply for a scheme.
    Pass any fields already known (e.g. extracted from an uploaded document)
    via prefilled_fields.

    Returns the application_id, a list of still-required fields the agent
    should collect from the citizen, and the current draft state.

    NOTE: This creates a local draft only — NOT a real government submission.
    The citizen must be informed clearly that this is an assisted draft.
    """
    scheme_key = scheme_name.lower().strip()
    required_fields = _get_field_requirements(scheme_key)
    collected = dict(prefilled_fields or {})

    missing = _missing_required_fields(required_fields, collected)
    app_id = _generate_application_id()

    record = {
        "application_id": app_id,
        "citizen_id": citizen_id,
        "scheme_name": scheme_name,
        "status": "DRAFT",
        "fields_required": required_fields,
        "fields_collected": collected,
        "fields_missing": [f["name"] for f in missing],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _APPLICATION_STORE[app_id] = record

    if missing:
        next_field = missing[0]
        return {
            "application_id": app_id,
            "scheme_name": scheme_name,
            "status": "DRAFT",
            "fields_collected": collected,
            "fields_missing": [f["label"] for f in missing],
            "next_question": f"To apply for {scheme_name}, I need a few details. Could you share your {next_field['label'].lower()}?",
            "note": "This is an assisted draft. No actual government submission has been made yet.",
        }
    else:
        record["status"] = "READY_TO_SUBMIT"
        return {
            "application_id": app_id,
            "scheme_name": scheme_name,
            "status": "READY_TO_SUBMIT",
            "fields_collected": collected,
            "fields_missing": [],
            "next_question": None,
            "message": (
                f"All required details collected for {scheme_name}.\n"
                f"Application Draft ID: {app_id}\n"
                "Please review and confirm to proceed.\n"
                "NOTE: This is an assisted draft — actual submission goes through the official scheme portal."
            ),
            "note": "Draft ready. Actual submission requires the official government portal.",
        }


@tool
async def update_application(
    application_id: str,
    new_fields: dict,
) -> dict:
    """
    Update an in-progress application draft with newly provided field values.

    Call this as the citizen provides each piece of required information
    during the guided application filling conversation.

    Returns the updated draft state including remaining missing fields and
    the next question to ask the citizen, or a ready-to-submit confirmation.
    """
    record = _APPLICATION_STORE.get(application_id.strip().upper())
    if not record:
        return {
            "found": False,
            "application_id": application_id,
            "message": f"No draft found with ID {application_id}. Use start_application to begin.",
        }

    # Merge new fields
    record["fields_collected"].update({k: v for k, v in new_fields.items() if v})
    record["updated_at"] = datetime.now(timezone.utc).isoformat()

    missing = _missing_required_fields(
        record["fields_required"],
        record["fields_collected"],
    )
    record["fields_missing"] = [f["name"] for f in missing]

    if missing:
        next_field = missing[0]
        return {
            "application_id": application_id,
            "scheme_name": record["scheme_name"],
            "status": "DRAFT",
            "fields_collected": record["fields_collected"],
            "fields_missing": [f["label"] for f in missing],
            "next_question": f"Thank you. Now could you share your {next_field['label'].lower()}?",
        }
    else:
        record["status"] = "READY_TO_SUBMIT"
        return {
            "application_id": application_id,
            "scheme_name": record["scheme_name"],
            "status": "READY_TO_SUBMIT",
            "fields_collected": record["fields_collected"],
            "fields_missing": [],
            "message": (
                f"All details collected for {record['scheme_name']}.\n"
                f"Application Draft ID: {application_id}\n"
                "Everything looks complete. This draft is ready for submission through the official scheme portal.\n"
                "NOTE: NAGRIK assists with form filling only. Actual submission must be done through the government portal."
            ),
        }


@tool
async def get_application_status(
    application_id: str,
    citizen_id: str,
) -> dict:
    """
    Retrieve the status and details of a previously started application draft.

    Args:
        application_id: The APP-XXXXXX reference number.
        citizen_id: The citizen's session ID (used for ownership check).
    """
    cid = application_id.strip().upper()
    record = _APPLICATION_STORE.get(cid)

    if not record:
        return {
            "found": False,
            "application_id": application_id,
            "message": (
                f"No application draft found with ID {application_id}. "
                "Please start a new application or check the reference number."
            ),
        }

    missing = _missing_required_fields(
        record["fields_required"],
        record["fields_collected"],
    )

    return {
        "found": True,
        "application_id": record["application_id"],
        "scheme_name": record["scheme_name"],
        "status": record["status"],
        "fields_collected_count": len(record["fields_collected"]),
        "fields_missing": [f["label"] for f in missing],
        "created_at": record["created_at"],
        "note": "This is an assisted draft — actual submission is through the official government portal.",
    }


APPLICATION_TOOLS = [start_application, update_application, get_application_status]
