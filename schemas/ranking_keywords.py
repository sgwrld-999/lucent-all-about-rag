"""Pydantic model for ranking keywords used for chunk relevance ranking."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RankingKeywords(BaseModel):
    """Top financial keywords used to rank relevant chunks."""

    keywords: list[str] = Field(
        ...,
        description="Exactly 5 financial keywords related to the user query.",
        min_length=5,
        max_length=5,
    )