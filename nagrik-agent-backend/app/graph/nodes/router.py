"""
Intent detection node: the first real decision point in the graph.
Uses structured output (Pydantic) via get_llm() so downstream conditional
edges can branch reliably instead of parsing free text.
"""
from typing import Literal
from pydantic import BaseModel
from langchain_core.messages import SystemMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState

INTENT_SYSTEM_PROMPT = """You are an intent classifier for Nagrik, a Digital \
Citizen Companion. Classify the citizen's latest message into exactly one \
of: scheme_query, complaint, application, status_check, general.

- scheme_query: asking about government schemes, eligibility, benefits, comparisons.
- complaint: reporting a civic issue or grievance.
- application: wants to start/continue filling an application/form.
- status_check: checking status of an existing application or complaint.
- general: greetings, small talk, or anything not covered above.
"""


class IntentResult(BaseModel):
    intent: Literal["scheme_query", "complaint", "application", "status_check", "general"]
    confidence: float


async def router_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(IntentResult)

    last_user_message = state["messages"][-1].content if state.get("messages") else ""

    result: IntentResult = await structured_llm.ainvoke(
        [SystemMessage(content=INTENT_SYSTEM_PROMPT),
         ("user", last_user_message)]
    )

    return {"intent": result.intent}
