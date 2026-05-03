"""Graph builder for Corrective RAG workflow."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from lucent.states import CorrectiveRAGState

from .answer_node import make_answer_node
from .grade_node import make_grade_node
from .retrieve_node import make_retrieve_node
from .rewrite_query_node import make_rewrite_query_node
from .routing_node import route_after_grade
from .web_search_node import make_web_search_node


def build_corrective_rag_graph(llm, retrieval_tool, search_tool):
    """Build and compile Corrective RAG graph from modular nodes."""
    builder = StateGraph(CorrectiveRAGState)

    builder.add_node("retrieve", make_retrieve_node(retrieval_tool))
    builder.add_node("grade", make_grade_node(llm))
    builder.add_node("rewrite", make_rewrite_query_node(llm))
    builder.add_node("web_search", make_web_search_node(search_tool))
    builder.add_node("answer", make_answer_node(llm))

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges("grade", route_after_grade, ["rewrite", "answer"])
    builder.add_edge("rewrite", "web_search")
    builder.add_edge("web_search", "answer")
    builder.add_edge("answer", END)

    return builder.compile()
