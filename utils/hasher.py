"""Reusable ingestion helpers for PDF processing and vector-store writes."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any


def compute_file_hash(file_path: str, chunk_size: int = 4096) -> str:
    """Compute a deterministic SHA-256 hash for a file."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    sha256_hash = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def processed_hash(vector_store) -> tuple[set[str], dict[str, Any]]:
    """Return known file hashes from the vector store."""
    existing_docs = vector_store.get(
        where={"file_hash": {"$ne": ""}},
        include=["metadatas"],
    )
    metadatas = existing_docs.get("metadatas") or []
    processed_hashes = {
        metadata.get("file_hash")
        for metadata in metadatas
        if isinstance(metadata, dict)
        and isinstance(metadata.get("file_hash"), str)
        and metadata.get("file_hash")
    }
    return processed_hashes, existing_docs
