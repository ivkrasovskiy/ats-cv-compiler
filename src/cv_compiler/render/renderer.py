from __future__ import annotations

from cv_compiler.render.types import RenderRequest, RenderResult


def render_cv(request: RenderRequest) -> RenderResult:
    """Render a CV using a template-driven backend."""
    raise NotImplementedError
