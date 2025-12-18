from __future__ import annotations

from cv_compiler.select.types import SelectionResult


def format_selection_explanation(selection: SelectionResult) -> str:
    """Format a human-readable explanation for `cv explain`."""
    raise NotImplementedError
