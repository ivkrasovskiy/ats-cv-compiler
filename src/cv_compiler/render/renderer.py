"""
Rendering interface for CV output.

This module defines the `render_cv` entrypoint used by the pipeline to produce final artifacts.
Implementation is currently stubbed.
"""

from __future__ import annotations

from cv_compiler.render.types import RenderRequest, RenderResult


def render_cv(request: RenderRequest) -> RenderResult:
    """Render a CV using a template-driven backend."""
    raise NotImplementedError
