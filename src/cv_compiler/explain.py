"""
Formatting helpers for selection explanations.

Used by `cv explain` to turn structured selection results into a human-readable report.
Implementation is scaffolded and will be filled in alongside selection logic.
"""

from __future__ import annotations

from cv_compiler.select.types import SelectionResult


def format_selection_explanation(selection: SelectionResult) -> str:
    """Format a human-readable explanation for `cv explain`."""
    raise NotImplementedError
