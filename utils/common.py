"""Common runtime setup helpers shared across notebooks and backend modules."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings


DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_ENV_FILENAME = ".env"


def load_project_env(
    project_root: str | Path,
    env_filename: str = DEFAULT_ENV_FILENAME,
    override: bool = False,
) -> Path:
    """Load the project environment file and return its resolved path."""
    root = Path(project_root).resolve()
    env_path = root / env_filename

    if not env_path.is_file():
        raise FileNotFoundError(f"Environment file not found: {env_path}")

    load_dotenv(dotenv_path=env_path, override=override)
    return env_path


def create_chat_llm(
    model_name: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    temperature: float = 0.0,
):
    """Create an Ollama chat client."""
    cleaned_model = model_name.strip()
    if not cleaned_model:
        raise ValueError("model_name must be a non-empty string")

    return ChatOllama(
        model=cleaned_model,
        base_url=base_url,
        temperature=temperature,
    )


def create_embedding_model(
    model_name: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    num_ctx: int = 8192,
):
    """Create an Ollama embeddings client."""
    cleaned_model = model_name.strip()
    if not cleaned_model:
        raise ValueError("model_name must be a non-empty string")

    return OllamaEmbeddings(
        model=cleaned_model,
        base_url=base_url,
        num_ctx=num_ctx,
    )


def create_vector_store(
    embedding_model,
    persist_directory: str | Path,
    collection_name: str,
):
    """Create a Chroma vector store."""
    if embedding_model is None:
        raise ValueError("embedding_model must not be None")

    cleaned_collection_name = collection_name.strip()
    if not cleaned_collection_name:
        raise ValueError("collection_name must be a non-empty string")

    persist_path = Path(persist_directory)
    persist_path.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=cleaned_collection_name,
        embedding_function=embedding_model,
        persist_directory=str(persist_path),
    )
