"""Data models for PDF ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ParsedLink:
    label: str | None
    url: str | None


@dataclass(frozen=True, slots=True)
class ParsedProfile:
    name: str | None
    headline: str | None
    location: str | None
    email: str | None
    about_me: str | None
    links: tuple[ParsedLink, ...]


@dataclass(frozen=True, slots=True)
class ParsedExperience:
    company: str | None
    title: str | None
    location: str | None
    start_date: str | None
    end_date: str | None
    bullets: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedProject:
    name: str | None
    company: str | None
    role: str | None
    start_date: str | None
    end_date: str | None
    bullets: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedSkillCategory:
    name: str | None
    items: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedEducation:
    institution: str | None
    degree: str | None
    location: str | None
    start_date: str | None
    end_date: str | None


@dataclass(frozen=True, slots=True)
class ParsedCv:
    profile: ParsedProfile
    experience: tuple[ParsedExperience, ...]
    projects: tuple[ParsedProject, ...]
    skills: tuple[ParsedSkillCategory, ...]
    education: tuple[ParsedEducation, ...]


@dataclass(frozen=True, slots=True)
class IngestResult:
    written_paths: tuple[Path, ...]
    warnings: tuple[str, ...]
