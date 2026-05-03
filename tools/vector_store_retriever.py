"""Vector store retriever tool implementation."""

from __future__ import annotations

from typing import Any

from lucent.config.settings import Settings, get_settings
from lucent.interfaces import DocumentRetrievalTool


class VectorStoreRetriever(DocumentRetrievalTool):
    """Retrieve documents from vector store with filtering and reranking."""

    def __init__(self, settings: Settings | None = None):
        """Initialize with settings and lazy-load runtime dependencies."""
        self.settings = settings or get_settings()
        self._runtime: dict[str, Any] = {}

    def _ensure_runtime(self) -> dict[str, Any]:
        """Lazy-load and cache runtime dependencies."""
        if self._runtime:
            return self._runtime

        try:
            from lucent.retriever.retrieval import (
                extract_filters,
                generate_ranking_keywords,
                initialize_llm,
                rank_documents_by_keywords,
                search_vector_database,
            )
            from lucent.utils.common import create_embedding_model, create_vector_store
        except ModuleNotFoundError:
            from retriever.retrieval import (
                extract_filters,
                generate_ranking_keywords,
                initialize_llm,
                rank_documents_by_keywords,
                search_vector_database,
            )
            from utils.common import create_embedding_model, create_vector_store

        embedding_model = create_embedding_model(self.settings.embed_model, base_url=self.settings.base_url)
        vector_store = create_vector_store(
            embedding_model=embedding_model,
            persist_directory=self.settings.vector_db_dir,
            collection_name=self.settings.collection_name,
        )

        llm, _, selected_model = initialize_llm(
            preferred_model=self.settings.llm_model,
            base_url=self.settings.base_url,
        )

        self._runtime = {
            "llm": llm,
            "selected_model": selected_model,
            "vector_store": vector_store,
            "extract_filters": extract_filters,
            "generate_ranking_keywords": generate_ranking_keywords,
            "search_vector_database": search_vector_database,
            "rank_documents_by_keywords": rank_documents_by_keywords,
        }
        return self._runtime

    def invoke(self, query: str, k: int = 5, filters: dict[str, Any] | None = None) -> str:
        """Retrieve and rerank documents from vector store."""
        runtime = self._ensure_runtime()
        llm = runtime["llm"]
        vector_store = runtime["vector_store"]

        print(f"\n[RETRIEVAL] Query: {query}")

        extracted_filters = runtime["extract_filters"](llm, query)
        if filters:
            extracted_filters.update(filters)

        ranking_keywords = runtime["generate_ranking_keywords"](llm, query)

        results = runtime["search_vector_database"](
            vector_store=vector_store,
            query=query,
            filters=extracted_filters,
            ranking_keywords=ranking_keywords,
            k=max(10 * int(k), 10),
        )

        docs = runtime["rank_documents_by_keywords"](results, ranking_keywords, k=int(k))
        print(f"[RETRIEVAL] Retrieved {len(docs)} documents")

        if not docs:
            return f"No documents found for: '{query}'. Try rephrasing the query."

        blocks: list[str] = []
        for index, doc in enumerate(docs, start=1):
            lines = [f"--- Document {index} ---"]
            for key, value in doc.metadata.items():
                lines.append(f"{key}: {value}")
            lines.append(f"\nContent:\n{doc.page_content}")
            blocks.append("\n".join(lines))

        output = "\n\n".join(blocks)
        self._write_debug(output, "retrieved_docs.md", query)
        return output

    def _write_debug(self, content: str, filename: str, query: str) -> None:
        """Write debug output to file."""
        debug_dir = self.settings.ensure_debug_dir()
        debug_file = debug_dir / filename
        debug_file.write_text(f"Query: {query}\n\n{content}", encoding="utf-8")
