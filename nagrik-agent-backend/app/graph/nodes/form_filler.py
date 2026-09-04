"""
Application-creation subgraph logic. Given a target FormSchema, this node
looks at extracted_fields (populated by conversation extraction and/or
doc_understanding_node) plus the latest message, figures out what's still
missing, and either asks for the next missing field or, once complete,
submits the application.

Deliberately modality-agnostic: it only ever sees `extracted_fields` and
plain text `messages` -- never audio or images directly.
"""
import json
import re
from langchain_core.messages import AIMessage, HumanMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState
from app.schemas.forms import FormSchema


def _extract_json(text: str) -> dict:
    """Extract JSON dict from LLM text response."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


async def form_filler_node(state: AgentState, form_schema: FormSchema) -> dict:
    llm = get_llm(temperature=0)
    field_names = [f.name for f in form_schema.fields]

    # Collect conversation text for context
    convo_text = "\n".join(
        f"{msg.__class__.__name__}: {msg.content}"
        for msg in state["messages"]
        if hasattr(msg, "content") and isinstance(msg.content, str)
    )

    extract_prompt = (
        f"From this conversation, extract values for these form fields: {field_names}\n\n"
        f"Conversation:\n{convo_text}\n\n"
        f"Return ONLY a JSON object like: {{\"field_name\": \"value\", ...}}\n"
        f"Use null for fields not mentioned. Do not add extra keys."
    )
    try:
        response = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        raw = _extract_json(response.content)
        new_values = {k: v for k, v in raw.items() if v is not None and k in field_names}
    except Exception:
        new_values = {}

    merged = {**state.get("extracted_fields", {}), **new_values}

    missing = [f for f in form_schema.fields if f.required and not merged.get(f.name)]

    if missing:
        next_field = missing[0]
        prompt = f"Could you share your {next_field.label.lower()}?"
        return {
            "extracted_fields": merged,
            "active_form_schema": form_schema.model_dump(),
            "messages": [AIMessage(content=prompt)],
        }

    # All required fields collected — ready to submit.
    confirmation = (
        f"I have all the details needed for your {form_schema.title.lower()}. "
        f"Shall I submit it now?"
    )
    return {
        "extracted_fields": merged,
        "active_form_schema": form_schema.model_dump(),
        "messages": [AIMessage(content=confirmation)],
    }
