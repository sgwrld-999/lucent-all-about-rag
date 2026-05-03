"""Fiscal year utilities."""

from __future__ import annotations

from enum import Enum

class FiscalQuarter(str, Enum):
    """Supported fiscal quarters."""

    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"


