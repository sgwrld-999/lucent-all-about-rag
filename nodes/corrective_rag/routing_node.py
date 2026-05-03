"""Routing node for Corrective RAG."""

from __future__ import annotations


def route_after_grade(state) -> str:
    """Route to rewrite or answer depending on relevance and retry count."""
    is_relevant = state.get("is_relevant", False)
    retry_count = state.get("retry_count", 0)

    if is_relevant:
        print("[ROUTE] Relevant -> answer")
        return "answer"
    if retry_count < 1:
        print("[ROUTE] Not relevant -> rewrite once")
        return "rewrite"
    print("[ROUTE] Retry exhausted -> answer with best context")
    return "answer"
