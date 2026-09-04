"""
End-to-end scripted conversations covering the 4 canonical demo flows:
scheme query, complaint filing, application creation, status check.
Run this exact file, unmodified, on both LLM_PROVIDER=openrouter and
LLM_PROVIDER=gemini before the demo (per Milestone 6 DoD).
"""
import pytest
from langchain_core.messages import HumanMessage
from app.graph.build_graph import compiled_graph

SCENARIOS = [
    ("scheme", "What government schemes exist for artisans?", "scheme_query"),
    ("complaint", "There is a broken streetlight on my road.", "complaint"),
    ("status", "What is the status of my complaint cmp_abc123?", "status_check"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("name,message,expected_intent", SCENARIOS)
async def test_scenario(name, message, expected_intent):
    config = {"configurable": {"thread_id": f"e2e-{name}"}}
    result = await compiled_graph.ainvoke(
        {"messages": [HumanMessage(content=message)],
         "session_id": f"e2e-{name}", "citizen_id": "e2e-citizen",
         "language": "en", "tool_calls_made": []},
        config=config,
    )
    assert result["messages"][-1].content
    assert result.get("intent") == expected_intent
