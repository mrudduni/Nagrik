"""
Main response node. Binds domain tools (scheme/complaint/RAG) so the LLM
can decide when to call them, per LangGraph's standard tool-calling
pattern. Runs after routing so it can be given intent-specific context.
"""
from langchain_core.messages import SystemMessage
from app.llm.get_llm import get_llm
from app.schemas.agent_state import AgentState
from app.graph.tools.scheme_tools import SCHEME_TOOLS
from app.graph.tools.complaint_tools import COMPLAINT_TOOLS
from app.graph.tools.rag_tools import RAG_TOOLS

ALL_TOOLS = SCHEME_TOOLS + COMPLAINT_TOOLS + RAG_TOOLS

SYSTEM_PROMPT = """You are Nagrik, a helpful Digital Citizen Companion for \
Indian government services. You have tools to look up schemes, check \
eligibility, file/check complaints, and search a government-knowledge base \
(tree_rag_search). Always use tree_rag_search before answering factual \
questions about specific schemes/policies rather than relying on your own \
knowledge, since scheme details change and citizens need accurate answers. \
If the knowledge base returns no relevant result, say so honestly instead \
of guessing. Keep replies concise and in plain language a citizen (not a \
policy expert) can understand.

When tree_rag_search returns chunks, ground the answer only in those chunks
and mention the scheme/source/page when available. Do not invent citations.

Detected intent for this turn: {intent}
"""


async def responder_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0.3)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    system = SystemMessage(content=SYSTEM_PROMPT.format(intent=state.get("intent", "general")))
    messages = [system] + state["messages"]

    response = await llm_with_tools.ainvoke(messages)

    tool_calls_made = state.get("tool_calls_made", [])
    if getattr(response, "tool_calls", None):
        tool_calls_made = tool_calls_made + [tc["name"] for tc in response.tool_calls]

    return {"messages": [response], "tool_calls_made": tool_calls_made}
