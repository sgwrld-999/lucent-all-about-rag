"""Grade node for Corrective RAG."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GradeDecision(BaseModel):
    """Structured output for document relevance grading."""

    is_relevant: bool = Field(
        description="True if documents are relevant to answer the question."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")


def make_grade_node(llm):
    """Create a node that grades if retrieved docs are sufficient."""

    def grade_node(state):
        llm_structured = llm.with_structured_output(GradeDecision)
        user_question = state["messages"][-1].content
        retrieved_docs = state.get("retrieved_docs", "")

        prompt = f"""Evaluate if the retrieved documents can answer this question.

USER QUESTION: {user_question}

RETRIEVED DOCUMENTS:
{retrieved_docs}

CRITERIA:
- is_relevant=True: Documents contain sufficient information to answer.
- is_relevant=False: Documents are empty, off-topic, or insufficient.

Respond with JSON: {{\"is_relevant\": bool, \"reasoning\": \"...\"}}"""

        decision = llm_structured.invoke(prompt)
        print(f"[GRADE] relevant={decision.is_relevant}: {decision.reasoning}")
        return {"is_relevant": decision.is_relevant}

    return grade_node
