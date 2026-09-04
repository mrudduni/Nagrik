"""
Navigation-decision node: runs after the main response and decides
whether a structured frontend navigation action should accompany the
reply. Navigation is secondary to the conversation itself, so this never
blocks or overrides the text reply — it only augments it.
"""
from pydantic import BaseModel
from langchain_core.messages import SystemMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState
from app.schemas.chat import NavigationAction

NAV_SYSTEM_PROMPT = """Given the conversation so far and the assistant's \
latest reply, decide if a frontend navigation action should accompany the reply. \
Navigation should ONLY be proposed if the citizen explicitly requests to navigate, open a form, view details, compare, or track (e.g. "Take me to the application form", "Open comparison"). \
For general informational questions, document queries, or eligibility discussions, return action="none". \
If proposed, target_id must be a simple slug (e.g. "sch-ayushman", "sch-pmkisan", "sch-pmay-u"). Do not invent non-existent IDs. Return action="none" if unsure.
"""


async def navigation_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(NavigationAction)

    result: NavigationAction = await structured_llm.ainvoke(
        [SystemMessage(content=NAV_SYSTEM_PROMPT)] + state["messages"]
    )

    return {"navigation": result.model_dump()}
