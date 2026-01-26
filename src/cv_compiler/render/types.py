"""
Rendering request/response types.

These types describe what content to render, which templates to use, and where to write outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from cv_compiler.schema.models import CanonicalData
from cv_compiler.select.types import SelectionResult


class RenderFormat(str, Enum):
    PDF = "pdf"
    MARKDOWN = "md"


@dataclass(frozen=True, slots=True)
class RenderRequest:
    data: CanonicalData
    selection: SelectionResult
    template_dir: Path
    output_path: Path
    format: RenderFormat = RenderFormat.PDF
    markdown_path: Path | None = None
    highlighted_skills: tuple[str, ...] = ()
    skills_filter: tuple[str, ...] = ()
    experience_summary: str | None = None


@dataclass(frozen=True, slots=True)
class RenderResult:
    output_path: Path
    markdown_path: Path
    pdf_path: Path | None
