from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv_compiler.llm.base import LLMProvider
from cv_compiler.render.types import RenderFormat
from cv_compiler.types import LintIssue


@dataclass(frozen=True, slots=True)
class BuildRequest:
    data_dir: Path
    job_path: Path | None
    template_dir: Path
    out_dir: Path
    format: RenderFormat = RenderFormat.PDF
    llm: LLMProvider | None = None
    llm_instructions_path: Path | None = None


@dataclass(frozen=True, slots=True)
class BuildResult:
    output_path: Path
    issues: tuple[LintIssue, ...]


def build_cv(request: BuildRequest) -> BuildResult:
    """
    Pipeline: parse → validate → select → (optional rewrite) → render → lint.

    The default behavior MUST be deterministic and MUST NOT require network access.
    """
    raise NotImplementedError
