"""
Image/document understanding node.

Citizens can upload photos of IDs, scanned forms, scheme posters,
notices, certificates, screenshots, and other government documents.

Images are analyzed by a vision-capable LLM.
PDFs are processed with PyMuPDF text extraction.

The extracted content is returned as `extracted_text` and can then
be passed to the main NAGRIK agent for answering the citizen's query.
"""

import base64

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.get_llm import get_vision_llm
from app.schemas.agent_state import AgentState


DOC_SYSTEM_PROMPT = """
You are NAGRIK's government document and image understanding assistant.

Analyze uploaded government documents, forms, certificates, scheme
posters, notices, screenshots, IDs, and other images.

Your job is to accurately understand the information visible in the
uploaded image.

Always:

- Read all clearly visible text.
- Identify what type of document or image this is.
- Extract important names, dates, amounts, scheme names, eligibility
  criteria, benefits, instructions, application information, and
  identifiers when visible.
- Explain the important information contained in the image.
- Preserve important numbers, dates, names, and scheme names accurately.
- If the image contains a government scheme or notice, explain it in
  simple language.
- Never invent information that is not visible.
- If something is unreadable, say that it is unreadable rather than
  guessing.
"""


def _decode_base64_payload(data: str) -> bytes:
    """
    Decode either plain base64 or a data URL containing base64.
    """

    if "," in data and data.strip().startswith("data:"):
        data = data.split(",", 1)[1]

    return base64.b64decode(data)


def _extract_pdf_text(document_base64: str) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    """

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF text extraction."
        ) from exc

    pdf_bytes = _decode_base64_payload(
        document_base64
    )

    with fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as doc:

        pages = [
            page.get_text().strip()
            for page in doc
        ]

    return "\n\n".join(
        page
        for page in pages
        if page
    )


async def doc_understanding_node(
    state: AgentState,
    image_base64: str,
    mime_type: str = "image/jpeg",
) -> dict:

    # ============================================================
    # PDF
    # ============================================================

    if mime_type == "application/pdf":

        extracted_text = _extract_pdf_text(
            image_base64
        )

        print(
            "========== DOCUMENT UNDERSTANDING =========="
        )
        print("MIME TYPE:", mime_type)
        print(
            "EXTRACTED TEXT:",
            repr(extracted_text[:2000]),
        )
        print(
            "============================================"
        )

        return {
            "extracted_fields": state.get(
                "extracted_fields",
                {},
            ),
            "extracted_text": extracted_text,
        }

    # ============================================================
    # IMAGE VALIDATION
    # ============================================================

    if not mime_type.startswith("image/"):
        raise ValueError(
            f"Unsupported document MIME type: {mime_type}. "
            "Only images and application/pdf are supported."
        )

    if not image_base64:
        raise ValueError(
            "Image data is empty."
        )

    # ============================================================
    # VISION MODEL
    # ============================================================

    llm = get_vision_llm()

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """
Analyze this uploaded image carefully.

Read and understand everything that is clearly visible.

Provide:

1. Complete readable text from the image.
2. The type or purpose of the document/image.
3. Important information contained in it.
4. Names, dates, amounts, scheme names, eligibility criteria,
   benefits, instructions, application details, or identifiers
   that are visible.
5. A simple explanation of what the image/document means.

If this is a government scheme poster, notice, form, certificate,
or document, explain the important information in simple language.

Do not invent information that is not visible.
If something cannot be read clearly, explicitly say so.
""",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:{mime_type};base64,"
                        f"{image_base64}"
                    )
                },
            },
        ]
    )

    # ============================================================
    # CALL VISION MODEL
    # ============================================================

    try:

        result = await llm.ainvoke(
            [
                SystemMessage(
                    content=DOC_SYSTEM_PROMPT
                ),
                message,
            ]
        )

        # LangChain normally returns a string here,
        # but handle other content types safely.
        if isinstance(result.content, str):

            extracted_text = (
                result.content.strip()
            )

        else:

            extracted_text = str(
                result.content
            ).strip()

    except Exception as exc:

        print(
            "========== DOCUMENT UNDERSTANDING ERROR =========="
        )
        print(
            "MIME TYPE:",
            mime_type,
        )
        print(
            "ERROR:",
            repr(exc),
        )
        print(
            "=================================================="
        )

        extracted_text = ""

    # ============================================================
    # DEBUG OUTPUT
    # ============================================================

    print(
        "========== DOCUMENT UNDERSTANDING =========="
    )

    print(
        "MIME TYPE:",
        mime_type,
    )

    print(
        "EXTRACTED TEXT:",
        repr(extracted_text),
    )

    print(
        "============================================"
    )

    # ============================================================
    # RETURN TO AGENT
    # ============================================================

    return {
        "extracted_fields": state.get(
            "extracted_fields",
            {},
        ),
        "extracted_text": extracted_text,
    }