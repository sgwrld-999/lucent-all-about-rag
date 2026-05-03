"""Web search node for Corrective RAG."""

from __future__ import annotations


def make_web_search_node(search_tool):
    """Create a node that fetches fallback web context."""

    def web_search_node(state):
        rewritten_query = state.get("rewritten_query") or state["messages"][-1].content
        web_docs = search_tool.invoke(query=rewritten_query, num_results=5)
        return {"retrieved_docs": web_docs}

    return web_search_node
