"""
Behavior tests for CV generation pipeline.

Uses examples/basic/data/ as a golden fixture (read-only).
All builds use llm=None or NoopProvider for determinism — no network calls.
Assertions are on observable state: files on disk, return values, issue severity.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from cv_compiler.llm.base import BulletRewriteResult, NoopProvider
from cv_compiler.pipeline import BuildRequest, build_cv
from cv_compiler.render.types import RenderFormat
from cv_compiler.types import Severity

_ROOT = Path(__file__).resolve().parents[1]
_DATA = _ROOT / "examples" / "basic" / "data"
_TEMPLATES = _ROOT / "examples" / "basic" / "templates"
_JOB = _ROOT / "examples" / "basic" / "jobs" / "backend_engineer.md"


def _req(
    out_dir: Path,
    *,
    data_dir: Path | None = None,
    job_path: Path | None = None,
    format: RenderFormat = RenderFormat.PDF,
    llm=None,
    render_from_markdown: Path | None = None,
) -> BuildRequest:
    return BuildRequest(
        data_dir=data_dir or _DATA,
        job_path=job_path,
        template_dir=_TEMPLATES,
        out_dir=out_dir,
        format=format,
        llm=llm,
        render_from_markdown=render_from_markdown,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── §1 PDF output ──────────────────────────────────────────────────────────────


def test_generic_build_produces_pdf(tmp_path):
    result = build_cv(_req(tmp_path))
    assert result.output_path.exists()
    assert result.output_path.name == "cv_generic.pdf"
    assert result.output_path.stat().st_size > 1024
    assert result.output_path.read_bytes().startswith(b"%PDF")


# ── §2 Markdown output ─────────────────────────────────────────────────────────


def test_generic_build_produces_markdown(tmp_path):
    result = build_cv(_req(tmp_path, format=RenderFormat.MARKDOWN))
    assert result.output_path.exists()
    assert result.output_path.name.endswith(".md")
    assert "Jordan Blake" in result.output_path.read_text(encoding="utf-8")


# ── §3 Job-targeted filename ───────────────────────────────────────────────────


def test_job_targeted_build_uses_job_id_in_filename(tmp_path):
    result = build_cv(_req(tmp_path, job_path=_JOB))
    assert result.output_path.exists()
    assert "generic" not in result.output_path.name


# ── §4 No errors on valid data ────────────────────────────────────────────────


def test_valid_build_has_no_error_issues(tmp_path):
    result = build_cv(_req(tmp_path))
    errors = [i for i in result.issues if i.severity == Severity.ERROR]
    assert errors == []


# ── §5 Missing profile ────────────────────────────────────────────────────────


def test_missing_profile_raises_or_returns_error(tmp_path):
    data_dir = tmp_path / "data"
    shutil.copytree(_DATA, data_dir)
    (data_dir / "profile.md").unlink()

    with pytest.raises((FileNotFoundError, ValueError)) as exc_info:
        build_cv(_req(tmp_path / "out", data_dir=data_dir))
    assert "profile" in str(exc_info.value).lower()


# ── §6 Render from markdown ───────────────────────────────────────────────────


def test_build_from_markdown_produces_pdf(tmp_path):
    md_path = tmp_path / "source.md"
    md_path.write_text("# Test CV\n\nHello World\n", encoding="utf-8")
    result = build_cv(_req(tmp_path / "out", render_from_markdown=md_path))
    assert result.output_path.exists()
    assert result.output_path.read_bytes().startswith(b"%PDF")


# ── §7 Nonexistent render_from_markdown raises ────────────────────────────────


def test_build_from_markdown_nonexistent_path_errors(tmp_path):
    with pytest.raises(ValueError):
        build_cv(_req(tmp_path, render_from_markdown=tmp_path / "ghost.md"))


# ── §8 NoopProvider identical to no LLM ──────────────────────────────────────


def test_noop_llm_produces_same_output_as_no_llm(tmp_path):
    r_none = build_cv(_req(tmp_path / "none"))
    r_noop = build_cv(_req(tmp_path / "noop", llm=NoopProvider()))
    assert _sha256(r_none.output_path) == _sha256(r_noop.output_path)


# ── §9 LLM failure is WARNING not ERROR ──────────────────────────────────────


class _FailProvider:
    """LLM that raises on all generative methods; rewrite passes through."""

    name = "fail"

    def rewrite_bullets(self, items, instructions):
        return [BulletRewriteResult(item_id=i.item_id, bullets=i.bullets) for i in items]

    def generate_experience(self, projects, job):
        raise RuntimeError("quota exceeded")

    def highlight_skills(self, skills, profile, job):
        raise RuntimeError("quota exceeded")

    def select_skills(self, skills_with_scores, profile, job):
        return [s for s, _, __ in skills_with_scores]

    def generate_experience_summary(self, projects, job):
        return ""

    def generate_cover_letter(self, profile, experience, job):
        return ""


def test_llm_failure_is_warning_not_error(tmp_path):
    result = build_cv(_req(tmp_path, llm=_FailProvider()))
    errors = [i for i in result.issues if i.severity == Severity.ERROR]
    warnings = [i for i in result.issues if i.severity == Severity.WARNING]
    assert errors == []
    assert len(warnings) > 0
    assert result.output_path.exists()


# ── §10 Deterministic output ──────────────────────────────────────────────────


def test_build_is_deterministic(tmp_path):
    r1 = build_cv(_req(tmp_path / "r1"))
    r2 = build_cv(_req(tmp_path / "r2"))
    assert _sha256(r1.output_path) == _sha256(r2.output_path)


# ── §11 Job build output — non-trivial content ────────────────────────────────


def test_job_build_output_is_non_trivial(tmp_path):
    result = build_cv(_req(tmp_path, job_path=_JOB, format=RenderFormat.MARKDOWN))
    assert result.output_path.stat().st_size > 200


# ── §12 Markdown output contains candidate name ───────────────────────────────


def test_markdown_output_contains_candidate_name(tmp_path):
    result = build_cv(_req(tmp_path, format=RenderFormat.MARKDOWN))
    assert "Jordan Blake" in result.output_path.read_text(encoding="utf-8")
