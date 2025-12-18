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


@dataclass(frozen=True, slots=True)
class RenderRequest:
    data: CanonicalData
    selection: SelectionResult
    template_dir: Path
    output_path: Path
    format: RenderFormat = RenderFormat.PDF


@dataclass(frozen=True, slots=True)
class RenderResult:
    output_path: Path
