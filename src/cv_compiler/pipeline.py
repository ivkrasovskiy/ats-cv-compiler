"""
Build pipeline request/response types and entrypoint.

The intended flow is: parse → validate → select → (optional rewrite) → render → lint.
Default behavior must remain deterministic; the pipeline implementation is currently scaffolded.
"""

from __future__ import annotations

import dataclasses
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from cv_compiler.lint.linter import lint_build_inputs, lint_rendered_output
from cv_compiler.llm.base import BulletRewriteRequest, LLMProvider
from cv_compiler.llm.experience import (
    archive_user_experience_files,
    backup_llm_experience_files,
    restore_llm_experience_files,
    write_experience_artifacts,
)
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.render.renderer import render_cv, render_markdown_to_pdf
from cv_compiler.render.types import RenderFormat, RenderRequest
from cv_compiler.schema.models import CanonicalData, JobSpec
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
    experience_regenerate: bool = False
    render_from_markdown: Path | None = None


_SKILL_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#-]*")
_MAX_JOB_SKILLS_PER_CATEGORY = 5


@dataclass(frozen=True, slots=True)
class BuildResult:
    output_path: Path
    markdown_path: Path | None
    pdf_path: Path | None
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
    if request.render_from_markdown is not None:
        markdown_path = request.render_from_markdown
        if not markdown_path.exists():
            raise ValueError(f"Markdown source not found: {markdown_path}")
        output_stem = _sanitize_stem(markdown_path.stem)
        if request.format == RenderFormat.PDF:
            output_path = request.out_dir / f"{output_stem}.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            render_markdown_to_pdf(markdown_path.read_text(encoding="utf-8"), output_path)
            issues = list(lint_rendered_output(output_path))
            return BuildResult(
                output_path=output_path,
                markdown_path=markdown_path,
                pdf_path=output_path,
                issues=tuple(issues),
            )
        issues = list(lint_rendered_output(markdown_path))
        return BuildResult(
            output_path=markdown_path,
            markdown_path=markdown_path,
            pdf_path=None,
            issues=tuple(issues),
        )

    data = load_canonical_data(request.data_dir)
    issues: list[LintIssue] = list(lint_build_inputs(data))

    job = load_job_spec(request.job_path) if request.job_path else None

    highlighted_skills: tuple[str, ...] = ()
    skills_filter: tuple[str, ...] = ()
    if request.llm is not None:
        try:
            if request.experience_regenerate:
                archive_user_experience_files(request.data_dir)
            drafts = request.llm.generate_experience(data.projects, job)
            if drafts:
                experience_warnings: list[str] = []
                backup_dir = backup_llm_experience_files(request.data_dir)
                try:
                    write_experience_artifacts(
                        request.data_dir,
                        projects=tuple(data.projects),
                        drafts=tuple(drafts),
                        warnings=experience_warnings,
                    )
                except Exception:
                    if backup_dir is not None:
                        restore_llm_experience_files(backup_dir, request.data_dir)
                    raise
                if backup_dir is not None:
                    shutil.rmtree(backup_dir, ignore_errors=True)
                data = load_canonical_data(request.data_dir)
                issues = list(lint_build_inputs(data))
                for warning in experience_warnings:
                    issues.append(
                        LintIssue(
                            code="LLM_EXPERIENCE_WARNING",
                            message=warning,
                            severity=Severity.WARNING,
                            source_path=None,
                        )
                    )
        except Exception as exc:  # noqa: BLE001
            issues.append(
                LintIssue(
                    code="LLM_GENERATION_FAILED",
                    message=str(exc),
                    severity=Severity.WARNING,
                    source_path=None,
                )
            )
        try:
            all_skills = tuple(item for cat in data.skills.categories for item in cat.items)
            if all_skills:
                highlighted_skills = tuple(
                    request.llm.highlight_skills(all_skills, data.profile, job)
                )
        except Exception as exc:  # noqa: BLE001
            issues.append(
                LintIssue(
                    code="LLM_SKILL_HIGHLIGHT_FAILED",
                    message=str(exc),
                    severity=Severity.WARNING,
                    source_path=None,
                )
            )
    if job is not None:
        if not highlighted_skills:
            categories = tuple((cat.name, cat.items) for cat in data.skills.categories)
            highlighted_skills = _deterministic_skill_highlights(categories, job)
        if highlighted_skills:
            skills_filter = highlighted_skills

    selection = select_content(data, job)

    if any(issue.severity == Severity.ERROR for issue in issues):
        output_stem = (
            "cv_generic"
            if request.job_path is None
            else f"cv_{_sanitize_stem(request.job_path.stem)}"
        )
        output_path = request.out_dir / f"{output_stem}.{request.format.value}"
        return BuildResult(
            output_path=output_path, markdown_path=None, pdf_path=None, issues=tuple(issues)
        )

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
            highlighted_skills=highlighted_skills,
            skills_filter=skills_filter,
        )
    )
    issues.extend(lint_rendered_output(render_result.output_path))
    return BuildResult(
        output_path=render_result.output_path,
        markdown_path=render_result.markdown_path,
        pdf_path=render_result.pdf_path,
        issues=tuple(issues),
    )


def _load_text_optional(path: Path | None) -> str | None:
    if path is None:
        return None
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _deterministic_skill_highlights(
    categories: tuple[tuple[str, tuple[str, ...]], ...],
    job: JobSpec,
) -> tuple[str, ...]:
    keyword_set = _job_keyword_set(job)
    selected: list[str] = []
    for _, items in categories:
        scored: list[tuple[int, int, str]] = []
        for idx, skill in enumerate(items):
            tokens = _tokenize_skill(skill)
            score = len(tokens & keyword_set)
            if score > 0:
                scored.append((score, idx, skill))
        scored.sort(key=lambda t: (-t[0], t[1], t[2].lower()))
        category_selected: list[str] = []
        seen: set[str] = set()
        for _, _, skill in scored:
            key = skill.strip().lower()
            if not key or key in seen:
                continue
            category_selected.append(skill)
            seen.add(key)
            if len(category_selected) >= _MAX_JOB_SKILLS_PER_CATEGORY:
                break
        selected.extend(category_selected)
    return tuple(selected)


def _job_keyword_set(job: JobSpec) -> set[str]:
    tokens = set(t.strip().lower() for t in job.keywords if t and t.strip())
    tokens.update(_SKILL_TOKEN_RE.findall(job.raw_text.lower()))
    if job.title:
        tokens.update(_SKILL_TOKEN_RE.findall(job.title.lower()))
    return {t for t in tokens if t}


def _tokenize_skill(skill: str) -> set[str]:
    return set(_SKILL_TOKEN_RE.findall(skill.lower()))
