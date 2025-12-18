from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from cv_compiler.schema.models import CanonicalData
from cv_compiler.types import LintIssue


def lint_build_inputs(data: CanonicalData) -> Sequence[LintIssue]:
    """Validate canonical data (schema + content constraints)."""
    raise NotImplementedError


def lint_rendered_output(output_path: Path) -> Sequence[LintIssue]:
    """Validate a rendered output artifact against ATS constraints."""
    raise NotImplementedError
