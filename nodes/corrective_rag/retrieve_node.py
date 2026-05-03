"""Retrieve node for Corrective RAG."""

from __future__ import annotations


def make_retrieve_node(retrieval_tool):
    """Create a node that retrieves documents for the user question."""

    def retrieve_node(state):
        user_question = state["messages"][-1].content
        docs_text = retrieval_tool.invoke(query=user_question, k=5)
        return {
            "retrieved_docs": docs_text,
            "retry_count": state.get("retry_count", 0),
        }

    return retrieve_node
