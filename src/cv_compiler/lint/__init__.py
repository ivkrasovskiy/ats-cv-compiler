"""
Linting entrypoints for inputs and outputs.

Linting enforces schema and ATS constraints, and is used by `cv lint` and the build pipeline.
"""

from __future__ import annotations

from .linter import lint_build_inputs, lint_rendered_output

__all__ = ["lint_build_inputs", "lint_rendered_output"]
