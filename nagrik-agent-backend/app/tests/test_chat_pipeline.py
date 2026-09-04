from langchain_core.messages import AIMessage, ToolMessage

from app.api.chat import _build_graph_text, _extract_sources


def test_build_graph_text_includes_message_ocr_and_fields():
    graph_text = _build_graph_text(
        "Tell me if I am eligible.",
        "Income: 120000",
        {"category": "OBC"},
    )

    assert "Tell me if I am eligible." in graph_text
    assert "Extracted document text" in graph_text
    assert "Income: 120000" in graph_text
    assert "category" in graph_text


def test_extract_sources_from_tree_rag_tool_message():
    result = {
        "messages": [
            AIMessage(content=""),
            ToolMessage(
                content={
                    "found": True,
                    "chunks": [
                        {
                            "text": "Relevant scheme chunk",
                            "scheme": "PM Vishwakarma",
                            "ministry": "Ministry of MSME",
                            "department": "MSME",
                            "source_file": "pm-vishwakarma.pdf",
                            "source_url": "https://pmvishwakarma.gov.in",
                            "page": 2,
                        }
                    ],
                },
                tool_call_id="call-1",
                name="tree_rag_search",
            ),
        ]
    }

    sources = _extract_sources(result)

    assert len(sources) == 1
    assert sources[0].scheme == "PM Vishwakarma"
    assert sources[0].page == 2
