"""Tests for cover letter generation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cv_compiler.llm.cover_letter import (
    build_cover_letter_prompt,
    parse_cover_letter,
)
from cv_compiler.schema.models import ExperienceEntry, JobSpec, Link, Profile


@pytest.fixture()
def sample_profile() -> Profile:
    return Profile(
        id="profile",
        name="Jordan Blake",
        headline="Senior Backend Engineer",
        location="Remote",
        email="jordan@example.com",
        links=(Link(label="GitHub", url="https://github.com/jordanblake"),),
        about_me="Builds distributed systems with a focus on reliability.",
    )


@pytest.fixture()
def sample_experience() -> tuple[ExperienceEntry, ...]:
    return (
        ExperienceEntry(
            id="exp_acme",
            company="Acme Corp",
            title="Software Engineer",
            location="Remote",
            start_date="2021-01",
            end_date="2023-06",
            tags=("python", "backend"),
            keywords=(),
            bullets=("Built internal API serving 10M requests/day.",),
        ),
    )


@pytest.fixture()
def sample_job() -> JobSpec:
    return JobSpec(
        id="techcorp",
        title="Backend Engineer",
        raw_text="We are looking for a backend engineer with Python experience.",
        keywords=("python", "backend", "api"),
    )


@pytest.fixture()
def prompt_path(tmp_path: Path) -> Path:
    p = tmp_path / "cover_letter_prompt.md"
    p.write_text(
        "Profile: {{PROFILE}}\nExperience: {{EXPERIENCE}}\nJob: {{JOB}}\nContext: {{JOB_CONTEXT}}\n",
        encoding="utf-8",
    )
    return p


# ── parse_cover_letter tests ──────────────────────────────────────────────────

def test_parse_cover_letter_valid():
    text = json.dumps({"cover_letter": "Dear Hiring Team,\n\nI am writing..."})
    result = parse_cover_letter(text)
    assert result == "Dear Hiring Team,\n\nI am writing..."


def test_parse_cover_letter_strips_whitespace():
    text = json.dumps({"cover_letter": "  Hello  "})
    assert parse_cover_letter(text) == "Hello"


def test_parse_cover_letter_invalid_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_cover_letter("not json")


def test_parse_cover_letter_missing_key():
    with pytest.raises(ValueError, match="cover_letter"):
        parse_cover_letter(json.dumps({"wrong_key": "value"}))


def test_parse_cover_letter_empty_string():
    with pytest.raises(ValueError, match="non-empty"):
        parse_cover_letter(json.dumps({"cover_letter": ""}))


def test_parse_cover_letter_not_object():
    with pytest.raises(ValueError, match="JSON object"):
        parse_cover_letter(json.dumps(["list", "not", "object"]))


# ── build_cover_letter_prompt tests ──────────────────────────────────────────

def test_build_cover_letter_prompt_contains_profile_name(
    prompt_path: Path,
    sample_profile: Profile,
    sample_experience: tuple[ExperienceEntry, ...],
    sample_job: JobSpec,
):
    result = build_cover_letter_prompt(
        prompt_path,
        profile=sample_profile,
        experience=sample_experience,
        job=sample_job,
    )
    assert "Jordan Blake" in result


def test_build_cover_letter_prompt_contains_job_id(
    prompt_path: Path,
    sample_profile: Profile,
    sample_experience: tuple[ExperienceEntry, ...],
    sample_job: JobSpec,
):
    result = build_cover_letter_prompt(
        prompt_path,
        profile=sample_profile,
        experience=sample_experience,
        job=sample_job,
    )
    assert "techcorp" in result


def test_build_cover_letter_prompt_no_unresolved_placeholders(
    prompt_path: Path,
    sample_profile: Profile,
    sample_experience: tuple[ExperienceEntry, ...],
    sample_job: JobSpec,
):
    result = build_cover_letter_prompt(
        prompt_path,
        profile=sample_profile,
        experience=sample_experience,
        job=sample_job,
    )
    assert "{{" not in result
