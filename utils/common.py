"""Common setup helpers for notebook workflows."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings


DEFAULT_COLLECTION_NAME = "financial_docs"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "llama3.2:latest"


def get_project_root(cwd: str | Path | None = None) -> Path:
    """Return the repository root from either `rag/` or `rag/notebooks/`."""
    project_root = Path(cwd or Path.cwd()).resolve()
    if project_root.name == "notebooks":
        project_root = project_root.parent
    return project_root


def load_project_env(project_root: str | Path | None = None) -> Path:
    """Load variables from the repository `.env` file."""
    root = get_project_root(project_root)
    env_path = root / ".env"
    load_dotenv(dotenv_path=env_path)
    return env_path


def get_chroma_directory(project_root: str | Path | None = None) -> str:
    """Return the persistent Chroma storage directory."""
    root = get_project_root(project_root)
    return str(root / "storage" / "chroma_db")


def create_embedding_model(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    num_ctx: int = 8192,
) -> OllamaEmbeddings:
    """Create the embedding model used by Chroma."""
    try:
        embedding_model = OllamaEmbeddings(
            model=model_name,
            base_url=base_url,
            num_ctx=num_ctx,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to initialize embeddings: {exc}") from exc

    if embedding_model is None:
        raise RuntimeError("Failed to initialize embeddings: model is None")

    return embedding_model


def create_vector_store(
    embedding_model: OllamaEmbeddings,
    persist_directory: str,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Chroma:
    """Create a Chroma vector store backed by the configured directory."""
    try:
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=persist_directory,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to initialize vector-db: {exc}") from exc

    if vector_store is None:
        raise RuntimeError("Failed to initialize vector-db: vector_store is None")

    return vector_store


def get_runtime_settings(project_root: str | Path | None = None) -> dict[str, str]:
    """Return common runtime configuration used across notebooks."""
    root = get_project_root(project_root)
    return {
        "project_root": str(root),
        "chroma_db": get_chroma_directory(root),
        "collection_name": DEFAULT_COLLECTION_NAME,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "base_url": os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "llm_model": os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL),
    }


def create_chat_llm(model_name: str, base_url: str) -> ChatOllama:
    """Instantiate a ChatOllama client for the provided model and host."""
    return ChatOllama(model=model_name, base_url=base_url)


def initialize_vector_store_runtime(
    project_root: str | Path | None = None,
    *,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    base_url: str | None = None,
    persist_directory: str | None = None,
    num_ctx: int = 8192,
) -> dict[str, object]:
    """Load env, create embeddings, and initialize the persistent vector store."""
    root = get_project_root(project_root)
    load_project_env(root)
    runtime_settings = get_runtime_settings(root)

    resolved_base_url = base_url or runtime_settings["base_url"]
    resolved_persist_directory = persist_directory or get_chroma_directory(root)

    embedding_model = create_embedding_model(
        model_name=embedding_model_name,
        base_url=resolved_base_url,
        num_ctx=num_ctx,
    )
    vector_store = create_vector_store(
        embedding_model=embedding_model,
        persist_directory=resolved_persist_directory,
        collection_name=collection_name,
    )

    return {
        "project_root": root,
        "embedding_model": embedding_model,
        "vector_store": vector_store,
        "collection_name": collection_name,
        "embedding_model_name": embedding_model_name,
        "base_url": resolved_base_url,
        "persist_directory": resolved_persist_directory,
    }
