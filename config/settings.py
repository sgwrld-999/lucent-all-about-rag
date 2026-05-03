"""Centralized configuration for Lucent RAG workflows."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from lucent.utils.common import DEFAULT_BASE_URL


class Settings:
    """Application settings with environment variable overrides."""

    def __init__(self, workspace_root: Path | None = None):
        """Initialize settings from environment and workspace."""
        if workspace_root:
            env_path = workspace_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        
        self.workspace_root = workspace_root or self._detect_workspace_root()
        self.lucent_root = (
            self.workspace_root / "lucent"
            if (self.workspace_root / "lucent").is_dir()
            else self.workspace_root
        )

        # Model configuration
        self.llm_model = os.getenv("OLLAMA_LLM_MODEL", "qwen3")
        self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL)

        # Vector store configuration
        self.collection_name = os.getenv("CHROMA_COLLECTION", "financial_reports")
        self.vector_db_dir = self.lucent_root / "storage" / "chroma_financial_db"

        # Output configuration
        self.debug_logs_dir = self.lucent_root / "debug_logs"

    @staticmethod
    def _detect_workspace_root() -> Path:
        """Auto-detect workspace root from current working directory."""
        cwd = Path.cwd().resolve()
        return next(
            (p for p in [cwd, *cwd.parents] if (p / "lucent").is_dir()),
            cwd,
        )

    def ensure_debug_dir(self) -> Path:
        """Ensure debug logs directory exists."""
        self.debug_logs_dir.mkdir(parents=True, exist_ok=True)
        return self.debug_logs_dir

    def __repr__(self) -> str:
        return (
            f"Settings(llm_model={self.llm_model}, "
            f"embed_model={self.embed_model}, "
            f"base_url={self.base_url}, "
            f"workspace={self.workspace_root})"
        )


_GLOBAL_SETTINGS: Settings | None = None


def get_settings(workspace_root: Path | None = None) -> Settings:
    """Get or create global settings singleton."""
    global _GLOBAL_SETTINGS
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = Settings(workspace_root)
    return _GLOBAL_SETTINGS


def reset_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _GLOBAL_SETTINGS
    _GLOBAL_SETTINGS = None
