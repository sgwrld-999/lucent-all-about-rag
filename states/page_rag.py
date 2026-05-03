""" Page RAG state definitions. """

from __future__ import annotations

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class PageRAGState(TypedDict):
    """State passed through the Page RAG workflow."""

    messages: Annotated[list, add_messages]