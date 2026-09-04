"""
Basic graph tests. Run with: pytest app/tests/test_graph.py
Requires a valid LLM_PROVIDER API key in .env to actually hit a model;
these are integration-style tests by design (per the project's testing
approach of validating real behavior at each stage).
"""
import pytest
from langchain_core.messages import HumanMessage
from app.graph.build_graph import compiled_graph


@pytest.mark.asyncio
async def test_basic_chat_roundtrip():
    config = {"configurable": {"thread_id": "test-session-1"}}
    result = await compiled_graph.ainvoke(
        {
            "messages": [HumanMessage(content="Hello, what can you help me with?")],
            "session_id": "test-session-1",
            "citizen_id": "citizen-1",
            "language": "en",
            "tool_calls_made": [],
        },
        config=config,
    )
    assert result["messages"][-1].content
    assert result.get("intent") == "general"


@pytest.mark.asyncio
async def test_memory_persists_across_turns():
    config = {"configurable": {"thread_id": "test-session-2"}}
    await compiled_graph.ainvoke(
        {"messages": [HumanMessage(content="My name is Ravi.")],
         "session_id": "test-session-2", "citizen_id": "citizen-2",
         "language": "en", "tool_calls_made": []},
        config=config,
    )
    result = await compiled_graph.ainvoke(
        {"messages": [HumanMessage(content="What is my name?")],
         "session_id": "test-session-2", "citizen_id": "citizen-2",
         "language": "en", "tool_calls_made": []},
        config=config,
    )
    assert "ravi" in result["messages"][-1].content.lower()


@pytest.mark.asyncio
async def test_scheme_query_routes_correctly():
    config = {"configurable": {"thread_id": "test-session-3"}}
    result = await compiled_graph.ainvoke(
        {"messages": [HumanMessage(content="What schemes are available for artisans?")],
         "session_id": "test-session-3", "citizen_id": "citizen-3",
         "language": "en", "tool_calls_made": []},
        config=config,
    )
    assert result.get("intent") == "scheme_query"
