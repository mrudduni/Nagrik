"""
Image/document understanding node. Citizens can upload a photo of an ID
card, a scanned form, etc.; this extracts structured fields and merges
them into `extracted_fields` on the state, where the form-filler subgraph
can pick them up — no voice- or image-specific branching happens beyond
this single node.
"""
import base64

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


def _decode_base64_payload(data: str) -> bytes:
    if "," in data and data.strip().startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def _extract_pdf_text(document_base64: str) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF text extraction.") from exc

    pdf_bytes = _decode_base64_payload(document_base64)
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text().strip() for page in doc]
    return "\n\n".join(page for page in pages if page)


async def doc_understanding_node(
    state: AgentState,
    image_base64: str,
    mime_type: str = "image/jpeg",
) -> dict:

    # ---------- PDF ----------
    if mime_type == "application/pdf":
        extracted_text = _extract_pdf_text(image_base64)

        return {
            "extracted_fields": state.get("extracted_fields", {}),
            "extracted_text": extracted_text,
        }

    # ---------- IMAGE ----------
    if not mime_type.startswith("image/"):
        raise ValueError(
            f"Unsupported document MIME type: {mime_type}. "
            "Only images and application/pdf are supported."
        )

    llm = get_vision_llm()
    structured_llm = llm.with_structured_output(ExtractedDocFields)

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "Extract fields from this document.",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_base64}"
                },
            },
        ]
    )

    result: ExtractedDocFields = await structured_llm.ainvoke(
        [
            SystemMessage(content=DOC_SYSTEM_PROMPT),
            message,
        ]
    )

    merged_fields = {
        **state.get("extracted_fields", {}),
        **result.fields,
    }

    extracted_text = result.text or ""

    if result.doc_type:
        extracted_text = (
            f"Document type: {result.doc_type}\n"
            f"{extracted_text}"
        ).strip()

    return {
        "extracted_fields": merged_fields,
        "extracted_text": extracted_text,
    }