"""
Deterministic selection interface.

Given canonical data and an optional job spec, produces a stable selection result and traceable
decision records. Implementation is currently stubbed.
"""

from __future__ import annotations

from cv_compiler.schema.models import CanonicalData, JobSpec
from cv_compiler.select.types import SelectionResult


def select_content(data: CanonicalData, job: JobSpec | None) -> SelectionResult:
    """
    Deterministically select which items to include in the CV.

    If `job` is None, selection should still be deterministic and produce a reasonable generic CV.
    """
    raise NotImplementedError
