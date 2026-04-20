from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DocType(str, Enum):
    TEN_K = "10-k"
    TEN_Q = "10-q"
    EIGHT_K = "8-k"
    OTHER = "other"


class FiscalQuarter(str, Enum):
    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"


class ChunkMetadata(BaseModel):
    company_name: Optional[str] = Field(
        default=None,
        description="Company name in lowercase, for example: 'amazon', 'apple', 'google'.",
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


class RankingKeywords(BaseModel):
    keywords: list[str] = Field(
        ...,
        description="Exactly 5 financial keywords related to user query",
        min_length=5,
        max_length=5,
    )