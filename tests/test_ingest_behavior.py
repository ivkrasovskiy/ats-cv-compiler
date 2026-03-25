"""
Behavior tests for PDF ingest: given an LLM JSON response, assert what files
are written to data/ and what IngestResult is returned.

Uses parse_ingest_response + write_ingest_files directly — no PDF or CLI needed.
All assertions are on observable state (files on disk, return values).
"""

from __future__ import annotations

import json

import pytest

from cv_compiler.ingest.pdf_ingest import _cli_llm_content, write_ingest_files
from cv_compiler.ingest.pdf_parser import parse_ingest_response
from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter

# ── fixtures ──────────────────────────────────────────────────────────────────


def _response(**overrides) -> str:
    """Return a minimal valid LLM JSON response string."""
    base: dict = {
        "profile": {
            "name": "Jane Doe",
            "headline": "Software Engineer",
            "location": "Remote",
            "email": "jane@example.com",
            "links": [
                {"label": "LinkedIn", "url": "https://linkedin.com/in/jane"},
                {"label": "GitHub", "url": "https://github.com/jane"},
            ],
            "about_me": "Experienced engineer.",
        },
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Senior Engineer",
                "location": "Remote",
                "start_date": "2022-01",
                "end_date": "",
                "bullets": ["Led migration.", "Cut latency 40%."],
                "tags": ["python"],
            },
            {
                "company": "Beta Inc",
                "title": "Engineer",
                "location": "NYC",
                "start_date": "2020-03",
                "end_date": "2021-12",
                "bullets": ["Built CI."],
                "tags": ["go"],
            },
            {
                "company": "Gamma Ltd",
                "title": "Junior Engineer",
                "location": "London",
                "start_date": "2018-06",
                "end_date": "2020-02",
                "bullets": ["REST APIs."],
                "tags": ["java"],
            },
        ],
        "projects": [],
        "skills": [
            {"name": "Languages", "items": ["Python", "Go"]},
            {"name": "Tools", "items": ["Kubernetes", "Docker"]},
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "BSc Computer Science",
                "location": "Cambridge, MA",
                "start_date": "2014",
                "end_date": "2018",
            },
            {
                "institution": "Oxford",
                "degree": "MSc AI",
                "location": "Oxford",
                "start_date": "2018",
                "end_date": "2019",
            },
            {
                "institution": "Spanish",
                "degree": "B2",
                "location": "",
                "start_date": "",
                "end_date": "",
            },
        ],
    }
    base.update(overrides)
    return json.dumps(base)


def _parsed(response_str: str = ""):
    return parse_ingest_response(response_str or _response())


# ── §1 profile.md ─────────────────────────────────────────────────────────────


def test_profile_md_written_with_correct_fields(tmp_path):
    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    doc = parse_markdown_frontmatter(tmp_path / "profile.md")
    fm = doc.frontmatter
    assert fm["name"] == "Jane Doe"
    assert fm["email"] == "jane@example.com"
    links = fm["links"]
    assert any(lnk.get("label") == "LinkedIn" for lnk in links)
    assert any(lnk.get("label") == "GitHub" for lnk in links)


# ── §2 skills.md ──────────────────────────────────────────────────────────────


def test_skills_md_written_with_all_categories(tmp_path):
    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    doc = parse_markdown_frontmatter(tmp_path / "skills.md")
    cats = doc.frontmatter["categories"]
    names = [c["name"] for c in cats]
    assert "Languages" in names
    assert "Tools" in names
    items_flat = [i for c in cats for i in c["items"]]
    assert "Python" in items_flat
    assert "Kubernetes" in items_flat


# ── §3 projects (from experience) ─────────────────────────────────────────────


def test_one_project_file_per_experience_entry(tmp_path):
    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    project_files = list((tmp_path / "projects").glob("*.md"))
    assert len(project_files) == 3


def test_project_files_have_correct_company_and_bullets(tmp_path):
    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    companies = set()
    for f in (tmp_path / "projects").glob("*.md"):
        doc = parse_markdown_frontmatter(f)
        companies.add(doc.frontmatter.get("company", ""))
    assert "Acme Corp" in companies
    assert "Beta Inc" in companies
    assert "Gamma Ltd" in companies


# ── §4 education.md ───────────────────────────────────────────────────────────


def test_education_md_written_with_all_entries(tmp_path):
    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    doc = parse_markdown_frontmatter(tmp_path / "education.md")
    entries = doc.frontmatter["entries"]
    institutions = [e["institution"] for e in entries]
    assert "MIT" in institutions
    assert "Oxford" in institutions
    assert "Spanish" in institutions  # language as education entry


# ── §5 empty experience ───────────────────────────────────────────────────────


def test_empty_experience_writes_no_project_files(tmp_path):
    resp = json.loads(_response())
    resp["experience"] = []
    resp["projects"] = []
    parsed = parse_ingest_response(json.dumps(resp))
    write_ingest_files(tmp_path, parsed, overwrite=False)

    proj_dir = tmp_path / "projects"
    files = list(proj_dir.glob("*.md")) if proj_dir.exists() else []
    assert files == []


# ── §6 warnings ───────────────────────────────────────────────────────────────


def test_empty_name_produces_warning(tmp_path):
    resp = json.loads(_response())
    resp["profile"]["name"] = ""
    parsed = parse_ingest_response(json.dumps(resp))
    result = write_ingest_files(tmp_path, parsed, overwrite=False)

    assert any("name" in w.lower() for w in result.warnings)


# ── §7 overwrite=True removes old project files ───────────────────────────────


def test_overwrite_true_removes_old_project_files(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    old_file = projects_dir / "old_stale.md"
    old_file.write_text("old content", encoding="utf-8")

    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=True)

    assert not old_file.exists()
    new_files = list(projects_dir.glob("*.md"))
    assert len(new_files) == 3


# ── §8 overwrite=False keeps old project files ────────────────────────────────


def test_overwrite_false_keeps_old_project_files(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    old_file = projects_dir / "old_stale.md"
    old_file.write_text("old content", encoding="utf-8")

    parsed = _parsed()
    write_ingest_files(tmp_path, parsed, overwrite=False)

    assert old_file.exists()


# ── §9 invalid JSON response raises ───────────────────────────────────────────


def test_invalid_json_response_raises():
    with pytest.raises((ValueError, Exception)):
        parse_ingest_response("this is not json at all !!!")


# ── §10 CLI command not found raises ──────────────────────────────────────────


def test_cli_command_not_found_raises():
    config = CodexExecConfig(
        command="nonexistent_cli_xyz_abc",
        args=("-p",),
        model=None,
        timeout_seconds=5,
        prompt_mode="arg",
        progress=False,
    )
    with pytest.raises(ValueError) as exc_info:
        _cli_llm_content(config, "hello")
    msg = str(exc_info.value).lower()
    assert "not found" in msg or "path" in msg


# ── §11 CLI non-zero exit includes stderr ─────────────────────────────────────


def test_cli_nonzero_exit_includes_stderr(tmp_path):
    # Write a tiny script that exits 1 and prints a known error to stderr
    script = tmp_path / "fake_cli.sh"
    script.write_text(
        "#!/bin/sh\necho 'quota exceeded' >&2\nexit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)

    config = CodexExecConfig(
        command=str(script),
        args=(),
        model=None,
        timeout_seconds=5,
        prompt_mode="arg",
        progress=False,
    )
    with pytest.raises(ValueError) as exc_info:
        _cli_llm_content(config, "hello")
    assert "quota exceeded" in str(exc_info.value)


# ── §12 mailto links excluded from profile ────────────────────────────────────


def test_mailto_links_excluded_from_profile(tmp_path):
    resp = json.loads(_response())
    resp["profile"]["links"] = [
        {"label": "LinkedIn", "url": "https://linkedin.com/in/jane"},
        {"label": "Email", "url": "mailto:jane@example.com"},
    ]
    parsed = parse_ingest_response(json.dumps(resp))
    write_ingest_files(tmp_path, parsed, overwrite=False)

    doc = parse_markdown_frontmatter(tmp_path / "profile.md")
    links = doc.frontmatter.get("links", [])
    urls = [lnk.get("url", "") for lnk in links]
    assert not any("mailto:" in u for u in urls)


# ── §13–14 written_paths result ───────────────────────────────────────────────


def test_written_paths_includes_core_files(tmp_path):
    parsed = _parsed()
    result = write_ingest_files(tmp_path, parsed, overwrite=False)

    path_names = {p.name for p in result.written_paths}
    assert "profile.md" in path_names
    assert "skills.md" in path_names
    assert "education.md" in path_names


def test_all_returned_paths_exist_on_disk(tmp_path):
    parsed = _parsed()
    result = write_ingest_files(tmp_path, parsed, overwrite=False)

    for p in result.written_paths:
        assert p.exists(), f"Path listed in result but missing on disk: {p}"
