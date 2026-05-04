"""Reusable ingestion helpers for PDF processing and vector-store writes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from interfaces.base import Invokable
from utils.extractor import extract_metadata_from_filename, extract_pdf_page_wise
from utils.hasher import compute_file_hash, processed_hash


class PageIngestion(Invokable[str | Path, list[dict[str, Any]]]):
    def invoke(self, vector_store: Any, source_path: str | Path) -> list[dict[str, Any]]:
        """
        Execute the PDF ingestion pipeline for a file or directory.

        Args:
            vector_store: The vector database client/instance.
            source_path: Path to a single PDF file or a directory containing PDFs.

        Returns:
            A list of result dictionaries containing the ingestion status
            for each processed file.
        """
        path = Path(source_path)
        results = []

        if path.is_file():
            if path.suffix.lower() != ".pdf":
                print(f"[WARNING] Skipping non-PDF file: {path}")
                return results
            # Process a single file
            results.append(self._ingest_single_pdf(vector_store, str(path)))

        elif path.is_dir():
            # Process all PDFs in the directory (recursively)
            for pdf_file in path.rglob("*.pdf"):
                try:
                    result = self._ingest_single_pdf(vector_store, str(pdf_file))
                    results.append(result)
                except Exception as exc:
                    print(f"[ERROR] Failed to process {pdf_file.name}: {exc}")
                    results.append(
                        {
                            "status": "failed",
                            "file_path": str(pdf_file),
                            "error": str(exc),
                        }
                    )
        else:
            raise FileNotFoundError(f"Source path not found: {source_path}")

        return results

    def _ingest_single_pdf(self, vector_store: Any, file_path: str) -> dict[str, Any]:
        """
        Private method to ingest a single PDF into the vector store with duplicate detection.
        """
        path = Path(file_path)

        file_hash = compute_file_hash(file_path=str(path))
        processed_hashes_set, _ = processed_hash(vector_store)

        if file_hash in processed_hashes_set:
            print(f"[SKIP] File already processed: {file_path} (hash: {file_hash})")
            return {
                "status": "skipped",
                "file_hash": file_hash,
                "reason": "duplicate",
                "pages_added": 0,
            }

        pages = extract_pdf_page_wise(str(path))
        file_metadata = extract_metadata_from_filename(path.name)

        processed_pages: list[Document] = []
        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue

            metadata_dict = file_metadata.copy()
            metadata_dict["page"] = page_num
            metadata_dict["file_hash"] = file_hash
            metadata_dict["source_file"] = str(path)

            processed_pages.append(
                Document(page_content=page_text, metadata=metadata_dict)
            )

        if not processed_pages:
            raise ValueError(f"No non-empty pages were extracted from: {file_path}")

        vector_store.add_documents(documents=processed_pages)
        return {
            "status": "completed",
            "file_hash": file_hash,
            "pages_added": len(processed_pages),
        }


def embedding_ingestion_vector_db(vector_store: Any, file_path: str) -> dict[str, Any]:
    """Backward-compatible wrapper for single-file PDF ingestion."""
    return PageIngestion()._ingest_single_pdf(vector_store, file_path)


def extract_metedata_from_file_name(filename: str) -> dict[str, Any]:
    """Backward-compatible alias for the previous misspelled helper name."""
    return extract_metadata_from_filename(filename)
