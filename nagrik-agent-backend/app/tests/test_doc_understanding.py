"""
Doc-understanding node test. Requires a sample base64 image and a
vision-capable model configured. Placeholder assertion structure —
plug in a real test image before Day 8.
"""
import pytest
from app.graph.nodes.doc_understanding import doc_understanding_node

SAMPLE_BASE64_IMAGE = ""  # TODO: paste a small sample ID/form image base64 here


@pytest.mark.asyncio
@pytest.mark.skipif(not SAMPLE_BASE64_IMAGE, reason="Add a sample image before running")
async def test_extracts_fields_from_sample_doc():
    result = await doc_understanding_node(
        state={"extracted_fields": {}},
        image_base64=SAMPLE_BASE64_IMAGE,
        mime_type="image/jpeg",
    )
    assert isinstance(result["extracted_fields"], dict)
