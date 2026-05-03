"""Retriever tool node for the Page RAG workflow."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool


SYSTEM_DEBUG_FILENAME = "retrieved_reranked_docs.md"


def create_retrieve_docs_tool(
    llm,
    vector_store,
    extract_filters,
    generate_ranking_keywords,
    search_vector_database,
    rank_documents_by_keywords,
    *,
    debug_dir: str | Path = "debug_logs",
):
    """Create a LangChain tool that retrieves and reranks financial documents."""

    debug_path = Path(debug_dir)

    @tool
    def retrieve_docs(query: str, k: int = 5) -> str:
        """Retrieve financial documents from ChromaDB with reranking."""
        print("\n[TOOL] retrieve_docs called")
        print(f"[QUERY] {query}")

        filters = extract_filters(llm, query)
        ranking_keywords = generate_ranking_keywords(llm, query)

        results = search_vector_database(
            vector_store=vector_store,
            query=query,
            filters=filters,
            ranking_keywords=ranking_keywords,
            k=max(10 * k, 10),
        )

        docs = rank_documents_by_keywords(results, ranking_keywords, k=k)
        print(f"[RETRIEVED] {len(docs)} documents")

        if not docs:
            return f"No documents found for the query: '{query}'. Try rephrasing or relaxing filters."

        retrieved_text: list[str] = []
        for index, doc in enumerate(docs, start=1):
            doc_text = [f"--- Document {index} ---"]
            for key, value in doc.metadata.items():
                doc_text.append(f"{key}: {value}")
            doc_text.append(f"\nContent:\n{doc.page_content}")
            retrieved_text.append("\n".join(doc_text))

        output = "\n".join(retrieved_text)
        debug_path.mkdir(parents=True, exist_ok=True)
        (debug_path / SYSTEM_DEBUG_FILENAME).write_text(output, encoding="utf-8")
        return output

    return retrieve_docs
