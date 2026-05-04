"""Reusable ingestion utility function"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter

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
