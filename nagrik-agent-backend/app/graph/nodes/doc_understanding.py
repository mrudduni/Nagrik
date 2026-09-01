"""
Image/document understanding node. Citizens can upload a photo of an ID
card, a scanned form, etc.; this extracts structured fields and merges
them into `extracted_fields` on the state, where the form-filler subgraph
can pick them up — no voice- or image-specific branching happens beyond
this single node.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from app.llm.get_llm import get_vision_llm
from app.schemas.agent_state import AgentState
from app.schemas.forms import ExtractedDocFields

DOC_SYSTEM_PROMPT = """Extract structured information from the attached \
government document/ID/form image. Identify the document type and any \
clearly legible fields (name, date of birth, ID numbers, address, income, \
category, etc.). If a field is not clearly visible, omit it rather than \
guessing. Set confidence to your honest estimate of extraction reliability \
(0 to 1)."""


async def doc_understanding_node(state: AgentState, image_base64: str, mime_type: str = "image/jpeg") -> dict:
    llm = get_vision_llm()
    structured_llm = llm.with_structured_output(ExtractedDocFields)

    message = HumanMessage(content=[
        {"type": "text", "text": "Extract fields from this document."},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
    ])

    result: ExtractedDocFields = await structured_llm.ainvoke(
        [SystemMessage(content=DOC_SYSTEM_PROMPT), message]
    )

    merged_fields = {**state.get("extracted_fields", {}), **result.fields}
    return {"extracted_fields": merged_fields}
