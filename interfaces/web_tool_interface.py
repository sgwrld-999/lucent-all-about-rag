
"""Web search tool interface."""

from .tools_interface import Tool


class WebSearchTool(Tool):
    """Interface for web search across the internet."""

    def invoke(self, query: str, num_results: int = 5) -> str:
        """Search the web for information.
        
        Args:
            query: Search query string.
            num_results: Number of results to return (default: 5).
        
        Returns:
            Formatted search results as string.
        """
        raise NotImplementedError("Subclasses must implement invoke()")