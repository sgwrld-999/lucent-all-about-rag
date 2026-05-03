"""Pydantic model for dataset chunk metadata"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fiscal_year import FiscalQuarter
from doc_type import DocType



class ChunkMetadata(BaseModel):
    """Metadata describing a chunk of financial document text."""

    company_name: Optional[str] = Field(
        default=None,
        description=(
            "Company name in lowercase, for example: "
            "'amazon', 'apple', 'google'."
        ),
    )
    doc_type: Optional[DocType] = Field(
        default=None,
        description="Document type such as 10-k, 10-q, or 8-k.",
    )
    fiscal_quarter: Optional[FiscalQuarter] = Field(
        default=None,
        description="Fiscal quarter of the document.",
    )
    fiscal_year: Optional[int] = Field(
        default=None,
        ge=1950,
        le=2050,
        description="Fiscal year of the document.",
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("company_name")
    @classmethod
    def normalize_company_name(cls, value: Optional[str]) -> Optional[str]:
        """Normalize company name to lowercase and trimmed text."""
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None


