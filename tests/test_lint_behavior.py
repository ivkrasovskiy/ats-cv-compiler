"""
Behavior tests for data loading and lint.

Uses temp copies of examples/basic/data/ with targeted mutations.
Assertions are on observable state: LintIssue severity/codes, raised exceptions.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cv_compiler.lint.linter import lint_build_inputs
from cv_compiler.parse.loaders import load_canonical_data
from cv_compiler.types import Severity

_ROOT = Path(__file__).resolve().parents[1]
_EXAMPLES_DATA = _ROOT / "examples" / "basic" / "data"


def _copy(dest: Path) -> Path:
    shutil.copytree(_EXAMPLES_DATA, dest)
    return dest


# ── §1 Valid example has no errors ────────────────────────────────────────────


def test_valid_example_has_no_errors():
    data = load_canonical_data(_EXAMPLES_DATA)
    issues = lint_build_inputs(data)
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert errors == []


# ── §2 Missing name → load raises ─────────────────────────────────────────────


def test_missing_name_produces_error(tmp_path):
    data_dir = _copy(tmp_path / "data")
    profile_path = data_dir / "profile.md"
    text = profile_path.read_text(encoding="utf-8")
    # Blank out the name field
    text = text.replace('name: "Jordan Blake"', 'name: ""')
    profile_path.write_text(text, encoding="utf-8")

    with pytest.raises((ValueError, FileNotFoundError)) as exc_info:
        load_canonical_data(data_dir)
    assert "name" in str(exc_info.value).lower()


# ── §3 Duplicate experience IDs produce ERROR ─────────────────────────────────


def test_duplicate_experience_ids_produces_error(tmp_path):
    data_dir = _copy(tmp_path / "data")
    exp_dir = data_dir / "experience"
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Two experience files with different base names but the same `id:` value
    entry = (
        "---\n"
        "id: shared_id\n"
        "company: FooCo\n"
        "title: Engineer\n"
        "start_date: 2020-01\n"
        "tags:\n  - python\n"
        "bullets:\n  - Did a thing.\n"
        "---\n"
    )
    (exp_dir / "user_alpha.md").write_text(entry, encoding="utf-8")
    (exp_dir / "user_beta.md").write_text(entry, encoding="utf-8")

    data = load_canonical_data(data_dir)
    issues = lint_build_inputs(data)
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert any("shared_id" in i.message or "duplicate" in i.message.lower() for i in errors)


# ── §4 Non-ASCII bullet produces WARNING ─────────────────────────────────────


def test_non_ascii_bullet_produces_warning(tmp_path):
    data_dir = _copy(tmp_path / "data")
    exp_dir = data_dir / "experience"
    exp_dir.mkdir(parents=True, exist_ok=True)

    entry = (
        "---\n"
        "id: exp_unicode_test\n"
        "company: FooCo\n"
        "title: Engineer\n"
        "start_date: 2021-01\n"
        "tags:\n  - python\n"
        'bullets:\n  - "Achieved 99% uptime \u2014 tr\u00e8s bon"\n'
        "---\n"
    )
    (exp_dir / "user_unicode_test.md").write_text(entry, encoding="utf-8")

    data = load_canonical_data(data_dir)
    issues = lint_build_inputs(data)
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert any("ascii" in i.message.lower() or "unicode" in i.message.lower() for i in warnings)


# ── §5 Missing skills file raises ─────────────────────────────────────────────


def test_missing_skills_file_raises(tmp_path):
    data_dir = _copy(tmp_path / "data")
    (data_dir / "skills.md").unlink()

    with pytest.raises((FileNotFoundError, ValueError)):
        load_canonical_data(data_dir)
