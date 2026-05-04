"""Reusable ingestion utility function"""

from __future__ import annotations

from pathlib import Path

from docling.document_converter import DocumentConverter

DOC_CONVERTER = DocumentConverter()


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
