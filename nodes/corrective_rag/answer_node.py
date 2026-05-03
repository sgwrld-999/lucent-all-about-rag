"""Answer node for Corrective RAG."""

from __future__ import annotations


def make_answer_node(llm):
    """Create a node that generates final answer from evidence."""

    def answer_node(state):
        user_question = state["messages"][-1].content
        retrieved_docs = state.get("retrieved_docs", "")

        prompt = f"""Answer using only the evidence provided.

QUESTION: {user_question}

EVIDENCE:
{retrieved_docs}

REQUIREMENTS:
1. Use markdown formatting (##, **, bullets, tables)
2. Include inline citations [1], [2], etc.
3. Add References section at end
4. If evidence insufficient, state clearly"""

        response = llm.invoke(prompt)
        return {"messages": [response]}

    return answer_node
