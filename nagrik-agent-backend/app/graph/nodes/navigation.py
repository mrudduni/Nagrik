"""
Navigation-decision node: runs after the main response and decides
whether a structured frontend navigation action should accompany the
reply. Uses plain text + JSON parsing to avoid Gemini model-prefilling
restrictions.
"""
import json
import re
from langchain_core.messages import HumanMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState
from app.schemas.chat import NavigationAction

NAV_PROMPT = """Given the assistant's latest reply below, decide if a frontend navigation action would help.

Valid actions: none, open_scheme_page, open_comparison, open_application_form, open_complaint_status, open_profile

Assistant reply: "{last_reply}"

Respond with ONLY valid JSON like:
{{"action": "none", "target_id": null}}

or if navigation is useful:
{{"action": "open_scheme_page", "target_id": "pm-kisan"}}

Only include target_id if you are certain of the value from the conversation. Otherwise use null."""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Extract from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Find first {...} in text
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"action": "none", "target_id": None, "label": None}


async def navigation_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    # Get the last AI message text
    last_reply = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.__class__.__name__ in ("AIMessage", "AIMessageChunk"):
            last_reply = str(msg.content)[:500]
            break

    if not last_reply:
        return {"navigation": NavigationAction(action="none").model_dump()}

    llm = get_llm(temperature=0)
    try:
        # Extract text safely
        if isinstance(last_reply, list):
            clean_parts = []
            for p in last_reply:
                if isinstance(p, dict) and "text" in p:
                    clean_parts.append(p["text"])
                elif isinstance(p, str):
                    clean_parts.append(p)
            last_reply = "\n".join(clean_parts)
        last_reply = str(last_reply)[:500]

        prompt_text = (
            "Given the assistant's latest reply below, determine if a specific external link or navigation action would be useful for the user.\n"
            "CRITICAL RULE: Default to action='none'. Only suggest an action if a specific scheme, comparison, application, or complaint was explicitly identified and discussed.\n"
            "Never suggest navigation for general explanations, advice, or multiple scheme overviews.\n\n"
            "Valid actions: none, open_scheme_page, open_comparison, open_application_form, open_complaint_status, open_profile\n\n"
            f'Assistant reply: "{last_reply}"\n\n'
            'Respond with ONLY valid JSON like: {"action": "none", "target_id": null}\n'
            'or if a specific scheme is clearly identified: {"action": "open_scheme_page", "target_id": "pm-kisan"}\n\n'
            "Only include target_id if you are certain of the exact slug/id from the conversation. Otherwise use action='none'."
        )

        response = await llm.ainvoke([HumanMessage(content=prompt_text)])
        data = _extract_json(response.content if isinstance(response.content, str) else str(response.content))

        valid_actions = {
            "none", "open_scheme_page", "open_comparison",
            "open_application_form", "open_complaint_status", "open_profile"
        }
        action = data.get("action", "none")
        if action not in valid_actions:
            action = "none"

        # If scheme page or application form is requested without a valid specific target_id, do not navigate
        target_id = data.get("target_id")
        if action in ("open_scheme_page", "open_application_form") and (not target_id or not str(target_id).strip() or str(target_id).lower() == "null"):
            action = "none"
            target_id = None

        nav = NavigationAction(
            action=action,
            target_id=target_id,
        )
        return {"navigation": nav.model_dump()}
    except Exception:
        return {"navigation": NavigationAction(action="none").model_dump()}

