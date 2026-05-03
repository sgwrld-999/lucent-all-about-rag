""" Supported SEC document types. """

from __future__ import annotations

from enum import Enum


class DocType(str, Enum):
    """Supported SEC document types."""

    TEN_K = "10-k"
    TEN_Q = "10-q"
    EIGHT_K = "8-k"
    OTHER = "other"
