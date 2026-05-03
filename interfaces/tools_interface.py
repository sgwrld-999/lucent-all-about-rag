"""Base tool interface."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Base interface for all RAG tools."""

    @abstractmethod
    def invoke(self, **kwargs) -> str:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters.
        
        Returns:
            Result as a formatted string.
        """
        pass