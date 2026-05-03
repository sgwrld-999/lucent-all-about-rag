"""Reusable ingestion helpers for PDF processing and vector-store writes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter
from langchain_core.documents import Document


DOC_CONVERTER = DocumentConverter()


def extract_metadata_from_filename(filename: str) -> dict[str, Any]:
    """Extract SEC-style metadata from a PDF filename."""
    stem = Path(filename).stem.strip().lower()
    parts = stem.split()

    if len(parts) < 3:
        raise ValueError(
            f"Invalid filename format: '{filename}'. "
            "Expected at least: {company_name} {doc_type} {year}.pdf"
        )

    metadata: dict[str, Any] = {
        "company_name": parts[0],
        "doc_type": None,
        "fiscal_quarter": None,
        "fiscal_year": None,
    }

    if parts[-1].isdigit() and len(parts[-1]) == 4:
        metadata["fiscal_year"] = int(parts.pop())

    if parts and parts[-1] in {"q1", "q2", "q3", "q4"}:
        metadata["fiscal_quarter"] = parts.pop().upper()

    if len(parts) >= 2:
        metadata["doc_type"] = " ".join(parts[1:])

    return metadata



def extract_pdf_page_wise(pdf_path: str) -> list[str]:
    """Convert a PDF into page-wise markdown chunks."""
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    try:
        converted_text = DOC_CONVERTER.convert(str(path))
    except Exception as exc:
        raise RuntimeError(f"Failed to convert PDF: {pdf_path}") from exc

    page_break = "<!-- page break -->"
    markdown_text = converted_text.document.export_to_markdown(
        page_break_placeholder=page_break
    )
    pages = [page.strip() for page in markdown_text.split(page_break)]
    return [page for page in pages if page]


def pdf_to_markdown(pdf_path: str, output_md_path: str | Path) -> Path:
    """Convert a PDF file into a Markdown file and return the output path."""
    pdf = Path(pdf_path)
    output_path = Path(output_md_path)

    if not pdf.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {pdf.suffix}")

    try:
        converted = DOC_CONVERTER.convert(str(pdf))
    except Exception as exc:
        raise RuntimeError(f"Failed to convert PDF: {pdf_path}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        converted.document.export_to_markdown(),
        encoding="utf-8",
    )
    return output_path


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


def embedding_ingestion_vector_db(vector_store, file_path: str) -> dict[str, Any]:
    """Ingest a PDF into the vector store with duplicate detection."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

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
    file_metadata = extract_metedata_from_file_name(path.name)

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


def pick_test_pdf(data_directory: str | Path, env_var: str = "ATTACHED_PDF_PATH") -> Path:
    """Pick a test PDF from the environment or the configured data directory."""
    attached = os.getenv(env_var, "").strip()
    if attached:
        path = Path(attached)
        if path.is_file() and path.suffix.lower() == ".pdf":
            return path
        raise FileNotFoundError(f"{env_var} is invalid: {attached}")

    pdfs = sorted(Path(data_directory).rglob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF found under DATA_DIRECTORY: {data_directory}")
    return pdfs[0]


def run_pipeline_tests(
    vector_store,
    data_directory: str | Path,
    pdf_path: str | None = None,
    run_full_tests: bool = True,
) -> dict[str, Any]:
    """Validate metadata extraction, hashing, page parsing, and ingestion."""
    report: dict[str, Any] = {
        "pdf": None,
        "mode": "full" if run_full_tests else "quick",
        "tests": {},
        "overall": "PASS",
    }

    path = Path(pdf_path) if pdf_path else pick_test_pdf(data_directory)
    report["pdf"] = str(path)

    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected an existing .pdf file, got: {path}")

    try:
        metadata = extract_metedata_from_file_name(path.name)
        expected_keys = {"company_name", "doc_type", "fiscal_quarter", "fiscal_year"}
        assert expected_keys.issubset(set(metadata.keys()))
        report["tests"]["metadata_extraction"] = {
            "status": "PASS",
            "metadata": metadata,
        }
    except Exception as exc:
        report["tests"]["metadata_extraction"] = {
            "status": "FAIL",
            "error": str(exc),
        }
        report["overall"] = "FAIL"

    try:
        first_hash = compute_file_hash(str(path))
        second_hash = compute_file_hash(str(path))
        assert first_hash == second_hash
        report["tests"]["hash_determinism"] = {
            "status": "PASS",
            "hash": first_hash,
        }
    except Exception as exc:
        report["tests"]["hash_determinism"] = {
            "status": "FAIL",
            "error": str(exc),
        }
        report["overall"] = "FAIL"

    try:
        processed_hashes_set, existing_docs = processed_hash(vector_store)
        assert isinstance(processed_hashes_set, set)
        assert isinstance(existing_docs, dict)
        report["tests"]["processed_hash"] = {
            "status": "PASS",
            "existing_hash_count": len(processed_hashes_set),
        }
    except Exception as exc:
        report["tests"]["processed_hash"] = {
            "status": "FAIL",
            "error": str(exc),
        }
        report["overall"] = "FAIL"

    if run_full_tests:
        try:
            pages = extract_pdf_page_wise(str(path))
            assert isinstance(pages, list)
            assert len(pages) > 0
            report["tests"]["page_extraction"] = {
                "status": "PASS",
                "pages": len(pages),
            }
        except Exception as exc:
            report["tests"]["page_extraction"] = {
                "status": "FAIL",
                "error": str(exc),
            }
            report["overall"] = "FAIL"

        try:
            first_run = embedding_ingestion_vector_db(vector_store, str(path))
            second_run = embedding_ingestion_vector_db(vector_store, str(path))
            assert first_run.get("status") in {"completed", "skipped"}
            assert second_run.get("status") == "skipped"
            report["tests"]["ingestion_and_dedup"] = {
                "status": "PASS",
                "first_run": first_run,
                "second_run": second_run,
            }
        except Exception as exc:
            report["tests"]["ingestion_and_dedup"] = {
                "status": "FAIL",
                "error": str(exc),
            }
            report["overall"] = "FAIL"

    return report
