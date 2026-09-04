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
latest reply, decide if a frontend navigation action would help the \
citizen. Only propose one if clearly useful (e.g. comparing schemes should \
open a comparison view; starting an application should open a form). \
Otherwise return action="none". Do not invent target_id values you don't \
have evidence for in the conversation — leave target_id null if unsure.
"""


async def navigation_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(NavigationAction)

    result: NavigationAction = await structured_llm.ainvoke(
        [SystemMessage(content=NAV_SYSTEM_PROMPT)] + state["messages"]
    )

    return {"navigation": result.model_dump()}
