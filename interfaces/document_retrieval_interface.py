"""Document retrieval tool interface."""

from typing import Any

from .tools_interface import Tool


class DocumentRetrievalTool(Tool):
    """Interface for document retrieval from vector store or external sources."""

    def invoke(self, query: str, k: int = 5, filters: dict[str, Any] | None = None) -> str:
        """Retrieve documents matching the query.
        
        Args:
            query: Search query string.
            k: Number of documents to retrieve (default: 5).
            filters: Optional metadata filters to apply.
        
        Returns:
            Formatted documents as string.
        """
        raise NotImplementedError("Subclasses must implement invoke()")