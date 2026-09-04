"""
LangChain tools wrapping Person 1's scheme API. Nodes call these; the
underlying client transparently switches between mock and real HTTP
calls based on USE_MOCK_BACKENDS.
"""
from langchain_core.tools import tool
from app.integrations.person1_client import person1_client


@tool
async def query_schemes(citizen_id: str) -> list[dict]:
    """Look up government schemes potentially relevant to a citizen."""
    return await person1_client.get_schemes(citizen_id)


@tool
async def check_eligibility(scheme_id: str, citizen_id: str) -> dict:
    """Check whether a citizen is eligible for a specific scheme."""
    return await person1_client.check_eligibility(scheme_id, citizen_id)


@tool
async def compare_schemes(scheme_ids: list[str]) -> dict:
    """Compare two or more schemes side by side."""
    return await person1_client.compare_schemes(scheme_ids)


SCHEME_TOOLS = [query_schemes, check_eligibility, compare_schemes]
