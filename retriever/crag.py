"""Corrective RAG (CRAG) orchestrator - tool and LLM agnostic."""

from __future__ import annotations

import operator
from typing import TypedDict, Annotated

from pydantic import BaseModel, Field

from lucent.interfaces import DocumentRetrievalTool, WebSearchTool


class GradeDecision(BaseModel):
    """Structured output for document relevance grading."""

    is_relevant: bool = Field(
        description="True if documents are relevant to answer the question."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")


class CRAGState(TypedDict):
    """State passed through CRAG workflow."""

    messages: Annotated[list, operator.add]
    retrieved_docs: str
    is_relevant: bool
    rewritten_query: str
    retry_count: int


class CRAG:
    """
    Corrective RAG orchestrator: retrieval → grading → rewrite (once) → web search → answer.
    
    Tools are injected as dependencies for testability and reusability.
    """

    def __init__(
        self,
        llm,
        retrieval_tool: DocumentRetrievalTool,
        search_tool: WebSearchTool,
    ):
        """
        Initialize CRAG with dependencies.
        
        Args:
            llm: Language model instance with structured output support.
            retrieval_tool: Tool for retrieving documents.
            search_tool: Tool for web search (fallback).
        """
        self.llm = llm
        self.retrieval_tool = retrieval_tool
        self.search_tool = search_tool

    def retrieve_node(self, state: CRAGState) -> dict:
        """Retrieve documents from vector store."""
        user_question = state["messages"][-1].content
        docs_text = self.retrieval_tool.invoke(query=user_question, k=5)
        return {
            "retrieved_docs": docs_text,
            "retry_count": state.get("retry_count", 0),
        }

    def grade_node(self, state: CRAGState) -> dict:
        """Grade document relevance to user question."""
        llm_structured = self.llm.with_structured_output(GradeDecision)
        user_question = state["messages"][-1].content
        retrieved_docs = state.get("retrieved_docs", "")

        prompt = f"""Evaluate if the retrieved documents can answer this question.

USER QUESTION: {user_question}

RETRIEVED DOCUMENTS:
{retrieved_docs}

CRITERIA:
- is_relevant=True: Documents contain sufficient information to answer.
- is_relevant=False: Documents are empty, off-topic, or insufficient.

Respond with JSON: {{"is_relevant": bool, "reasoning": "..."}}"""

        decision = llm_structured.invoke(prompt)
        print(f"[GRADE] relevant={decision.is_relevant}: {decision.reasoning}")
        return {"is_relevant": decision.is_relevant}

    def rewrite_query_node(self, state: CRAGState) -> dict:
        """Rewrite query for better retrieval."""
        user_question = state["messages"][-1].content
        prompt = f"""Rewrite for better financial document retrieval.

Original: {user_question}

Rules:
- Keep one clear sentence
- Include company names, years, quarters explicitly
- Use financial terms: revenue, income, cash flow, margin
- Return rewritten query only"""

        rewritten = self.llm.invoke(prompt).content.strip()
        next_retry = state.get("retry_count", 0) + 1
        print(f"[REWRITE] '{user_question}' → '{rewritten}'")
        return {
            "rewritten_query": rewritten,
            "retry_count": next_retry,
        }

    def web_search_node(self, state: CRAGState) -> dict:
        """Fallback web search with rewritten query."""
        rewritten_query = state.get("rewritten_query") or state["messages"][-1].content
        web_docs = self.search_tool.invoke(query=rewritten_query, num_results=5)
        return {"retrieved_docs": web_docs}

    def answer_node(self, state: CRAGState) -> dict:
        """Generate final answer from retrieved documents."""
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

        response = self.llm.invoke(prompt)
        return {"messages": [response]}

    def route_after_grade(self, state: CRAGState) -> str:
        """Router: send to rewrite or answer based on grade."""
        is_relevant = state.get("is_relevant", False)
        retry_count = state.get("retry_count", 0)

        if is_relevant:
            print("[ROUTE] Relevant → answer")
            return "answer"
        if retry_count < 1:
            print("[ROUTE] Not relevant → rewrite once")
            return "rewrite"
        print("[ROUTE] Retry exhausted → answer with best context")
        return "answer"

    def build_graph(self):
        """Build LangGraph state machine for CRAG workflow."""
        try:
            from langgraph.graph import StateGraph, START, END
        except ImportError:
            raise ImportError("langgraph required for CRAG.build_graph()")

        builder = StateGraph(CRAGState)

        builder.add_node("retrieve", self.retrieve_node)
        builder.add_node("grade", self.grade_node)
        builder.add_node("rewrite", self.rewrite_query_node)
        builder.add_node("web_search", self.web_search_node)
        builder.add_node("answer", self.answer_node)

        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "grade")
        builder.add_conditional_edges(
            "grade",
            self.route_after_grade,
            ["rewrite", "answer"],
        )
        builder.add_edge("rewrite", "web_search")
        builder.add_edge("web_search", "answer")
        builder.add_edge("answer", END)

        return builder.compile()
