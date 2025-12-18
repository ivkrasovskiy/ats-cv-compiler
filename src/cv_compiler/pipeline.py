"""
Build pipeline request/response types and entrypoint.

The intended flow is: parse → validate → select → (optional rewrite) → render → lint.
Default behavior must remain deterministic; the pipeline implementation is currently scaffolded.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

from cv_compiler.lint.linter import lint_build_inputs, lint_rendered_output
from cv_compiler.llm.base import BulletRewriteRequest, LLMProvider
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.render.renderer import render_cv
from cv_compiler.render.types import RenderFormat, RenderRequest
from cv_compiler.schema.models import CanonicalData
from cv_compiler.select.selector import select_content
from cv_compiler.types import LintIssue, Severity


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


def _sanitize_stem(stem: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem)
    return safe.strip("_") or "job"


def _apply_rewrites(data: CanonicalData, *, rewrites: dict[str, tuple[str, ...]]) -> CanonicalData:
    exp = []
    for e in data.experience:
        if e.id in rewrites:
            exp.append(dataclasses.replace(e, bullets=rewrites[e.id]))
        else:
            exp.append(e)

    proj = []
    for p in data.projects:
        if p.id in rewrites:
            proj.append(dataclasses.replace(p, bullets=rewrites[p.id]))
        else:
            proj.append(p)

    return dataclasses.replace(data, experience=tuple(exp), projects=tuple(proj))


def build_cv(request: BuildRequest) -> BuildResult:
    """
    Pipeline: parse → validate → select → (optional rewrite) → render → lint.

    The default behavior MUST be deterministic and MUST NOT require network access.
    """
    data = load_canonical_data(request.data_dir)
    issues: list[LintIssue] = list(lint_build_inputs(data))

    job = load_job_spec(request.job_path) if request.job_path else None
    selection = select_content(data, job)

    if any(issue.severity == Severity.ERROR for issue in issues):
        output_stem = (
            "cv_generic"
            if request.job_path is None
            else f"cv_{_sanitize_stem(request.job_path.stem)}"
        )
        output_path = request.out_dir / f"{output_stem}.{request.format.value}"
        return BuildResult(output_path=output_path, issues=tuple(issues))

    if request.llm is not None:
        job_keywords = job.keywords if job is not None else ()
        selected_ids = set(selection.selected_experience_ids) | set(selection.selected_project_ids)
        items = [
            BulletRewriteRequest(item_id=e.id, bullets=e.bullets, job_keywords=job_keywords)
            for e in data.experience
            if e.id in selected_ids
        ]
        items.extend(
            [
                BulletRewriteRequest(item_id=p.id, bullets=p.bullets, job_keywords=job_keywords)
                for p in data.projects
                if p.id in selected_ids
            ]
        )
        results = request.llm.rewrite_bullets(
            items, _load_text_optional(request.llm_instructions_path)
        )
        rewrites = {r.item_id: r.bullets for r in results}
        data = _apply_rewrites(data, rewrites=rewrites)

    output_stem = "cv_generic" if job is None else f"cv_{_sanitize_stem(job.id)}"
    output_path = request.out_dir / f"{output_stem}.{request.format.value}"

    render_result = render_cv(
        RenderRequest(
            data=data,
            selection=selection,
            template_dir=request.template_dir,
            output_path=output_path,
            format=request.format,
        )
    )
    issues.extend(lint_rendered_output(render_result.output_path))
    return BuildResult(output_path=render_result.output_path, issues=tuple(issues))


def _load_text_optional(path: Path | None) -> str | None:
    if path is None:
        return None
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
