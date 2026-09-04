"""
Assembles the central LangGraph agent.

Flow:
  entry -> router (intent detection)
        -> responder (may call tools: schemes/complaints/RAG)
        -> tools (ToolNode, if the responder requested any)
        -> back to responder if tools were called (standard ReAct loop)
        -> navigation (decide on a structured frontend action)
        -> END

Note: application/form-filling is a related but separate subgraph
(see nodes/form_filler.py) invoked directly by the /chat endpoint when
intent == "application" and an active form is in progress, rather than
wired as a graph edge here — this keeps the core conversational graph
simple while still sharing the same AgentState and LLM abstraction.
"""
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.schemas.agent_state import AgentState
from app.graph.nodes.router import router_node
from app.graph.nodes.responder import responder_node, ALL_TOOLS
from app.graph.nodes.navigation import navigation_node
from app.memory.checkpointer import get_checkpointer


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("responder", responder_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("navigation_node", navigation_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "responder")

    # Standard ReAct-style loop: if the responder asked for a tool call,
    # route to ToolNode and back; otherwise proceed to navigation.
    graph.add_conditional_edges(
        "responder",
        tools_condition,
        {"tools": "tools", END: "navigation_node"},
    )
    graph.add_edge("tools", "responder")
    graph.add_edge("navigation_node", END)

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)


# Built once at import time; FastAPI reuses this compiled graph across requests.
compiled_graph = build_graph()  
