"""
LangChain tools wrapping Person 3's complaint API.
"""
from langchain_core.tools import tool
from app.integrations.person3_client import person3_client


@tool
async def file_complaint(citizen_id: str, text: str) -> dict:
    """File a citizen grievance/complaint. Pass the raw complaint text;
    classification and routing happen on Person 3's backend."""
    return await person3_client.file_complaint(citizen_id=citizen_id, text=text)


@tool
async def check_complaint_status(complaint_id: str) -> dict:
    """Check the status of a previously filed complaint."""
    return await person3_client.check_status(complaint_id)


COMPLAINT_TOOLS = [file_complaint, check_complaint_status]
