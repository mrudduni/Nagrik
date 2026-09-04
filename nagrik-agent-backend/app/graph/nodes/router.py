"""
Intent detection node: the first real decision point in the graph.
Uses a plain LLM call with keyword parsing instead of structured output
to avoid Gemini 3.x model-prefilling restrictions.
"""
import re
from typing import Literal
from langchain_core.messages import HumanMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState

INTENT_PROMPT = """Classify the citizen's message into EXACTLY ONE of these categories:

scheme_query   - asking about government schemes, eligibility, benefits, subsidies
complaint      - reporting a civic issue (pothole, water, garbage, light, drainage, electricity)
application    - wants to fill/start/submit an application or form for a scheme
status_check   - checking status of a complaint (NGR-*) or application (APP-*)
general        - greetings, small talk, or anything else

Message: "{message}"

Reply with ONLY the category name. Nothing else. No explanation."""

VALID_INTENTS = {"scheme_query", "complaint", "application", "status_check", "general"}

KEYWORD_MAP = {
    "scheme_query": ["scheme", "yojana", "eligible", "benefit", "subsidy", "pension",
                     "kisan", "ayushman", "pm-", "ration", "scholarship", "welfare"],
    "complaint":    ["complaint", "pothole", "water", "garbage", "light", "drainage",
                     "electricity", "broken", "issue", "problem", "gutter", "road",
                     "shikayat", "pareshaan"],
    "application":  ["apply", "application", "form", "fill", "submit", "register",
                     "aavedan"],
    "status_check": ["status", "track", "ngr-", "app-", "check", "update"],
}


def _keyword_fallback(message: str) -> str:
    msg_lower = message.lower()
    for intent, keywords in KEYWORD_MAP.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "general"


async def router_node(state: AgentState) -> dict:
    last_user_message = state["messages"][-1].content if state.get("messages") else ""

    llm = get_llm(temperature=0)
    try:
        response = await llm.ainvoke(
            [HumanMessage(content=INTENT_PROMPT.format(message=last_user_message))]
        )
        # Extract the intent from response text
        text = response.content.strip().lower()
        # Try to find a valid intent token anywhere in the response
        for intent in VALID_INTENTS:
            if intent in text:
                return {"intent": intent}
        # Keyword fallback if LLM gave unexpected output
        return {"intent": _keyword_fallback(last_user_message)}
    except Exception:
        return {"intent": _keyword_fallback(last_user_message)}
