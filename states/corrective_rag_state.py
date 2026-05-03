""" Corrective RAG state definitions. """


from __future__ import annotations

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class CorrectiveRAGState(TypedDict):
    """State passed through the Corrective RAG workflow."""

    messages: Annotated[list, add_messages]
    retrieved_docs: str
    is_relevant: bool
    rewritten_query: str
    retry_count: int