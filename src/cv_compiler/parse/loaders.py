"""
Load canonical data and job specs from disk.

This module is responsible for turning repository files into validated in-memory models for the
pipeline. Functions are currently stubs (interfaces only).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from cv_compiler.parse.frontmatter import parse_markdown_frontmatter
from cv_compiler.schema.models import (
    CanonicalData,
    Education,
    EducationEntry,
    ExperienceEntry,
    JobSpec,
    Link,
    Profile,
    ProjectEntry,
    Skills,
    SkillsCategory,
)

_LLM_EXPERIENCE_PREFIX = "llm_"
_USER_EXPERIENCE_PREFIX = "user_"
_ACTIVE_USER_RE = re.compile(r"^user_[a-z0-9_]+$")
_ACTIVE_LLM_RE = re.compile(r"^llm_[a-z0-9_]+$")


def _require_mapping(
    frontmatter: Mapping[str, Any], key: str, *, source: Path
) -> Mapping[str, Any]:
    value = frontmatter.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"Missing or invalid `{key}` in {source}")
    return value


def _require_str(frontmatter: Mapping[str, Any], key: str, *, source: Path) -> str:
    value = frontmatter.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid `{key}` in {source}")
    return value.strip()


def _optional_str(frontmatter: Mapping[str, Any], key: str) -> str | None:
    value = frontmatter.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return None


def _optional_str_or_none(frontmatter: Mapping[str, Any], key: str) -> str | None:
    value = frontmatter.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return None


def _require_list_of_str(
    frontmatter: Mapping[str, Any], key: str, *, source: Path
) -> tuple[str, ...]:
    value = frontmatter.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"Missing or invalid `{key}` in {source}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Invalid `{key}` item in {source}")
        s = item.strip()
        if s:
            items.append(s)
    return tuple(items)


def _require_list_of_mapping(
    frontmatter: Mapping[str, Any], key: str, *, source: Path
) -> tuple[Mapping[str, Any], ...]:
    value = frontmatter.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"Missing or invalid `{key}` in {source}")
    out: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"Invalid `{key}` item in {source}")
        out.append(item)
    return tuple(out)


def _load_profile(path: Path) -> Profile:
    doc = parse_markdown_frontmatter(path)
    fm = doc.frontmatter
    profile_id = _require_str(fm, "id", source=path)
    name = _require_str(fm, "name", source=path)
    headline = _require_str(fm, "headline", source=path)
    location = _require_str(fm, "location", source=path)
    email = _optional_str(fm, "email")
    about_me = _require_str(fm, "about_me", source=path)
    link_items = _require_list_of_mapping(fm, "links", source=path)
    links: list[Link] = []
    for item in link_items:
        label = _require_str(item, "label", source=path)
        url = _require_str(item, "url", source=path)
        links.append(Link(label=label, url=url))
    return Profile(
        id=profile_id,
        name=name,
        headline=headline,
        location=location,
        email=email,
        links=tuple(links),
        about_me=about_me,
        source_path=path,
    )


def _load_experience_entry(path: Path) -> ExperienceEntry:
    doc = parse_markdown_frontmatter(path)
    fm = doc.frontmatter
    entry_id = _require_str(fm, "id", source=path)
    company = _require_str(fm, "company", source=path)
    title = _require_str(fm, "title", source=path)
    location = _optional_str_or_none(fm, "location")
    start_date = _require_str(fm, "start_date", source=path)
    end_date = _optional_str_or_none(fm, "end_date")
    tags = _require_list_of_str(fm, "tags", source=path)
    bullets = _require_list_of_str(fm, "bullets", source=path)
    return ExperienceEntry(
        id=entry_id,
        company=company,
        title=title,
        location=location,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        bullets=bullets,
        source_path=path,
    )


def _load_project_entry(path: Path) -> ProjectEntry:
    doc = parse_markdown_frontmatter(path)
    fm = doc.frontmatter
    entry_id = _require_str(fm, "id", source=path)
    name = _require_str(fm, "name", source=path)
    company = _optional_str_or_none(fm, "company")
    role = _optional_str_or_none(fm, "role")
    start_date = _optional_str_or_none(fm, "start_date")
    end_date = _optional_str_or_none(fm, "end_date")
    tags = _require_list_of_str(fm, "tags", source=path)
    bullets = _require_list_of_str(fm, "bullets", source=path)
    return ProjectEntry(
        id=entry_id,
        name=name,
        company=company,
        role=role,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        bullets=bullets,
        source_path=path,
    )


def _load_skills(path: Path) -> Skills:
    doc = parse_markdown_frontmatter(path)
    fm = doc.frontmatter
    skills_id = _require_str(fm, "id", source=path)
    cat_items = _require_list_of_mapping(fm, "categories", source=path)
    categories: list[SkillsCategory] = []
    for item in cat_items:
        name = _require_str(item, "name", source=path)
        items = _require_list_of_str(item, "items", source=path)
        categories.append(SkillsCategory(name=name, items=items))
    return Skills(id=skills_id, categories=tuple(categories), source_path=path)


def _load_education(path: Path) -> Education:
    doc = parse_markdown_frontmatter(path)
    fm = doc.frontmatter
    edu_id = _require_str(fm, "id", source=path)
    entry_items = _require_list_of_mapping(fm, "entries", source=path)
    entries: list[EducationEntry] = []
    for item in entry_items:
        institution = _require_str(item, "institution", source=path)
        degree = _require_str(item, "degree", source=path)
        location = _optional_str_or_none(item, "location")
        start_date = _optional_str_or_none(item, "start_date")
        end_date = _optional_str_or_none(item, "end_date")
        entries.append(
            EducationEntry(
                institution=institution,
                degree=degree,
                location=location,
                start_date=start_date,
                end_date=end_date,
            )
        )
    return Education(id=edu_id, entries=tuple(entries), source_path=path)


def load_canonical_data(data_dir: Path) -> CanonicalData:
    """Load and validate canonical data from a `data/` directory."""
    profile_path = data_dir / "profile.md"
    skills_path = data_dir / "skills.md"
    education_path = data_dir / "education.md"

    if not profile_path.exists():
        raise FileNotFoundError(f"Missing required file: {profile_path}")
    if not skills_path.exists():
        raise FileNotFoundError(f"Missing required file: {skills_path}")

    profile = _load_profile(profile_path)
    skills = _load_skills(skills_path)

    experience_dir = data_dir / "experience"
    experience: list[ExperienceEntry] = []
    if experience_dir.exists():
        for path in _select_experience_files(experience_dir):
            experience.append(_load_experience_entry(path))

    projects_dir = data_dir / "projects"
    projects: list[ProjectEntry] = []
    if projects_dir.exists():
        for path in sorted(projects_dir.glob("*.md")):
            projects.append(_load_project_entry(path))

    education: Education | None = None
    if education_path.exists():
        education = _load_education(education_path)

    return CanonicalData(
        profile=profile,
        experience=tuple(experience),
        projects=tuple(projects),
        skills=skills,
        education=education,
    )


def _select_experience_files(experience_dir: Path) -> list[Path]:
    candidates = list(experience_dir.glob("*.md"))
    best: dict[str, tuple[int, Path]] = {}
    for path in candidates:
        stem = path.stem
        base, priority = _experience_base_and_priority(stem)
        if priority <= 0:
            continue
        existing = best.get(base)
        if existing is None or priority > existing[0]:
            best[base] = (priority, path)
    return [best[k][1] for k in sorted(best.keys())]


def _experience_base_and_priority(stem: str) -> tuple[str, int]:
    if _ACTIVE_USER_RE.match(stem):
        return stem[len(_USER_EXPERIENCE_PREFIX) :], 2
    if _ACTIVE_LLM_RE.match(stem):
        return stem[len(_LLM_EXPERIENCE_PREFIX) :], 1
    return "", 0


def load_job_spec(path: Path) -> JobSpec:
    """Load a job spec from a Markdown or text file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".md":
        doc = parse_markdown_frontmatter(path)
        fm = doc.frontmatter
        job_id = _optional_str(fm, "id") or path.stem
        title = _optional_str_or_none(fm, "title")
        keywords: tuple[str, ...] = ()
        kw_val = fm.get("keywords")
        if isinstance(kw_val, Sequence) and not isinstance(kw_val, (str, bytes)):
            kws: list[str] = []
            for item in kw_val:
                if isinstance(item, str) and item.strip():
                    kws.append(item.strip())
            keywords = tuple(kws)
        return JobSpec(
            id=job_id,
            title=title,
            raw_text=doc.body.strip(),
            keywords=keywords,
            source_path=path,
        )

    return JobSpec(id=path.stem, title=None, raw_text=text.strip(), keywords=(), source_path=path)
