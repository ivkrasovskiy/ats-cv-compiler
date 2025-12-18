from __future__ import annotations

from cv_compiler.schema.models import CanonicalData, JobSpec
from cv_compiler.select.types import SelectionResult


def select_content(data: CanonicalData, job: JobSpec | None) -> SelectionResult:
    """
    Deterministically select which items to include in the CV.

    If `job` is None, selection should still be deterministic and produce a reasonable generic CV.
    """
    raise NotImplementedError
