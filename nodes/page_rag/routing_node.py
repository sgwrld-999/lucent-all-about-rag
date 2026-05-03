"""Routing node for the Page RAG workflow."""

from __future__ import annotations

from langgraph.graph import END


def should_continue(state) -> str:
    """Route to tools when the agent issued tool calls, otherwise stop."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END
