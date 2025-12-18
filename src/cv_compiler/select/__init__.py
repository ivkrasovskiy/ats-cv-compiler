"""
Deterministic selection API and result types.

Selection chooses which experience/projects are included for a generic build or a job-targeted
build, and records explainable decisions for `cv explain`.
"""

from __future__ import annotations

from .selector import select_content
from .types import SelectionDecision, SelectionResult

__all__ = ["SelectionDecision", "SelectionResult", "select_content"]
