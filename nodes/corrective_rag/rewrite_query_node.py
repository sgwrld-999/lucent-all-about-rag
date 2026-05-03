"""Rewrite query node for Corrective RAG."""

from __future__ import annotations


def make_rewrite_query_node(llm):
    """Create a node that rewrites the query for better retrieval."""

    def rewrite_query_node(state):
        user_question = state["messages"][-1].content
        prompt = f"""Rewrite for better financial document retrieval.

Original: {user_question}

Rules:
- Keep one clear sentence
- Include company names, years, quarters explicitly
- Use financial terms: revenue, income, cash flow, margin
- Return rewritten query only"""

        rewritten = llm.invoke(prompt).content.strip()
        next_retry = state.get("retry_count", 0) + 1
        print(f"[REWRITE] '{user_question}' -> '{rewritten}'")
        return {
            "rewritten_query": rewritten,
            "retry_count": next_retry,
        }

    return rewrite_query_node
