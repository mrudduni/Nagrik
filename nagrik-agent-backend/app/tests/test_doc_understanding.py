"""
Doc-understanding node test. Requires a sample base64 image and a
vision-capable model configured. Placeholder assertion structure —
plug in a real test image before Day 8.
"""
import pytest
from app.graph.nodes.doc_understanding import doc_understanding_node


class FakeStructuredVisionLLM:
    async def ainvoke(self, messages):
        from app.schemas.forms import ExtractedDocFields

        return ExtractedDocFields(
            doc_type="aadhaar",
            fields={"full_name": "Ravi Kumar"},
            text="Ravi Kumar",
            confidence=0.9,
        )


class FakeVisionLLM:
    def with_structured_output(self, schema):
        return FakeStructuredVisionLLM()


@pytest.mark.asyncio
async def test_extracts_fields_from_sample_doc(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.doc_understanding.get_vision_llm",
        lambda: FakeVisionLLM(),
    )

    result = await doc_understanding_node(
        state={"extracted_fields": {}},
        image_base64="ZmFrZS1pbWFnZQ==",
        mime_type="image/jpeg",
    )
    assert result["extracted_fields"]["full_name"] == "Ravi Kumar"
    assert "aadhaar" in result["extracted_text"]

