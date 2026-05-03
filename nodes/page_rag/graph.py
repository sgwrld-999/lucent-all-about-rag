"""Graph builder for the Page RAG workflow."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from lucent.states import PageRAGState


def build_page_rag_graph(agent_node, retrieve_docs_tool):
    """Build and compile the Page RAG graph."""
    from .routing_node import should_continue

    builder = StateGraph(PageRAGState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode([retrieve_docs_tool]))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")

    return builder.compile()
