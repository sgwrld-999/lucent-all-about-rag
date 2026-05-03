"""Factory for creating CRAG tools and orchestrator.

This module provides high-level helper functions for notebook usage,
keeping notebooks clean and focused on orchestration.
"""

from __future__ import annotations

import sys
from pathlib import Path

from lucent.config.settings import Settings, get_settings
from lucent.retriever.crag import CRAG
from lucent.tools.tools import DuckDuckGoSearcher, VectorStoreRetriever


def _setup_import_path() -> Path:
    """Add workspace root to import path for notebook execution."""
    cwd = Path.cwd().resolve()
    workspace_root = next(
        (p for p in [cwd, *cwd.parents] if (p / "lucent").is_dir()),
        cwd,
    )
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    return workspace_root


def create_retriever(settings: Settings | None = None) -> VectorStoreRetriever:
    """Create a vector store retriever.
    
    Args:
        settings: Optional Settings instance. If None, uses global settings.
    
    Returns:
        Configured VectorStoreRetriever instance.
    """
    return VectorStoreRetriever(settings or get_settings())


def create_web_searcher(settings: Settings | None = None) -> DuckDuckGoSearcher:
    """Create a web searcher.
    
    Args:
        settings: Optional Settings instance. If None, uses global settings.
    
    Returns:
        Configured DuckDuckGoSearcher instance.
    """
    return DuckDuckGoSearcher(settings or get_settings())


def create_crag_agent(
    llm,
    retriever: VectorStoreRetriever | None = None,
    searcher: DuckDuckGoSearcher | None = None,
) -> CRAG:
    """Create a CRAG agent with dependency injection.
    
    Args:
        llm: Language model instance with structured output support.
        retriever: Optional VectorStoreRetriever. If None, creates new.
        searcher: Optional DuckDuckGoSearcher. If None, creates new.
    
    Returns:
        Configured CRAG instance.
    """
    retriever = retriever or create_retriever()
    searcher = searcher or create_web_searcher()
    return CRAG(llm=llm, retrieval_tool=retriever, search_tool=searcher)
