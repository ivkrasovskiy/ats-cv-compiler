"""
Rendering interfaces for producing ATS-safe outputs.

Rendering is template-driven and should be reproducible on macOS/Linux. This package defines the
types and entrypoints used by the build pipeline.
"""

from __future__ import annotations

from .renderer import render_cv
from .types import RenderFormat, RenderRequest, RenderResult

__all__ = ["RenderFormat", "RenderRequest", "RenderResult", "render_cv"]
