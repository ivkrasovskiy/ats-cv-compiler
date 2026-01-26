"""
Dataclasses representing validated CV entities.

These types represent the canonical, renderable facts used by the compiler. Anything that appears
in output should be attributable to fields on these models (no fabrication).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Link:
    label: str
    url: str


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    name: str
    headline: str
    location: str
    email: str | None
    links: tuple[Link, ...]
    about_me: str
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ExperienceEntry:
    id: str
    company: str
    title: str
    location: str | None
    start_date: str
    end_date: str | None
    tags: tuple[str, ...]
    keywords: tuple[str, ...]
    bullets: tuple[str, ...]
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    id: str
    name: str
    company: str | None
    role: str | None
    start_date: str | None
    end_date: str | None
    tags: tuple[str, ...]
    bullets: tuple[str, ...]
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class SkillsCategory:
    name: str
    items: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Skills:
    id: str
    categories: tuple[SkillsCategory, ...]
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class EducationEntry:
    institution: str
    degree: str
    location: str | None
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True, slots=True)
class Education:
    id: str
    entries: tuple[EducationEntry, ...]
    languages: tuple[str, ...]
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class CanonicalData:
    profile: Profile
    experience: tuple[ExperienceEntry, ...]
    projects: tuple[ProjectEntry, ...]
    skills: Skills
    education: Education | None


@dataclass(frozen=True, slots=True)
class JobSpec:
    id: str
    title: str | None
    raw_text: str
    keywords: tuple[str, ...]
    source_path: Path | None = None
