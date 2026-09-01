"""
Application-creation subgraph logic. Given a target FormSchema, this node
looks at extracted_fields (populated by conversation extraction and/or
doc_understanding_node) plus the latest message, figures out what's still
missing, and either asks for the next missing field or, once complete,
submits the application.

Deliberately modality-agnostic: it only ever sees `extracted_fields` and
plain text `messages` — never audio or images directly.
"""
from pydantic import BaseModel, create_model
from langchain_core.messages import AIMessage, SystemMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState
from app.schemas.forms import FormSchema


def _build_extraction_model(schema: FormSchema) -> type[BaseModel]:
    fields = {f.name: (str | None, None) for f in schema.fields}
    return create_model("DynamicExtraction", **fields)


async def form_filler_node(state: AgentState, form_schema: FormSchema) -> dict:
    extraction_model = _build_extraction_model(form_schema)
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(extraction_model)

    extract_prompt = SystemMessage(content=(
        "Extract any values for the following form fields that the citizen "
        f"has provided so far in this conversation: {[f.name for f in form_schema.fields]}. "
        "Leave a field null if not mentioned."
    ))
    extracted = await structured_llm.ainvoke([extract_prompt] + state["messages"])
    new_values = {k: v for k, v in extracted.model_dump().items() if v is not None}

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
