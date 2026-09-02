"""
The single state object that flows through every LangGraph node.
Kept intentionally flat and modality-agnostic: by the time anything
reaches `messages`, it is plain text — STT/OCR have already happened
at the graph's edges (see multilingual/language_boundary.py and
graph/nodes/doc_understanding.py).
"""
from typing import Annotated, Any, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    session_id: str
    citizen_id: str
    language: str                     # original language of the citizen's input
    normalized_query: str             # English/pivot text used for routing, RAG, and LLM work
    original_message: str             # raw citizen text before translation/OCR normalization
    intent: Optional[Literal[
        "scheme_query", "complaint", "application", "status_check", "general"
    ]]
    extracted_fields: dict[str, Any]  # fields pulled from doc understanding / form filling
    extracted_text: str               # OCR/PDF text appended to the graph input
    active_form_schema: Optional[dict]
    navigation: Optional[dict]
    tool_calls_made: list[str]
    sources: list[dict[str, Any]]
