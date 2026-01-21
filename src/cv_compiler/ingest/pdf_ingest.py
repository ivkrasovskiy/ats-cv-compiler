"""
PDF ingestion helpers for bootstrapping canonical Markdown files.

Extracts machine-readable text, uses an LLM to structure it, and writes `.md` files under data/.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import yaml

from cv_compiler.llm.config import LLMConfig
from cv_compiler.llm.experience import USER_PREFIX
from cv_compiler.llm.openai import build_chat_endpoint, build_chat_payload, extract_chat_content

_SAFE_ID_RE = re.compile(r"[^a-z0-9_]+")
_MIN_TEXT_CHARS = 200
_PLACEHOLDER = "TODO: edit this field"


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


def extract_pdf_text(path: Path) -> str:
    """Extract text from a machine-readable PDF or raise if none is found."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("pypdf is required for PDF ingestion. Run `uv sync`.") from exc
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text)
    combined = "\n".join(chunks).strip()
    if len(re.sub(r"\s+", "", combined)) < _MIN_TEXT_CHARS:
        raise ValueError(
            "PDF contains too little extractable text; it may be scanned. "
            "Run OCR or provide a machine-readable PDF."
        )
    return combined


def ingest_pdf_to_markdown(
    *,
    data_dir: Path,
    pdf_path: Path,
    llm_mode: str,
    llm_config: LLMConfig | None,
    prompt_path: Path = Path("prompts/pdf_ingest_prompt.md"),
    overwrite: bool = False,
    request_path: Path | None = None,
    response_path: Path | None = None,
    manual_model: str = "manual",
    manual_base_url: str | None = None,
) -> IngestResult:
    """Convert a PDF CV into canonical Markdown files under `data_dir`."""
    text = extract_pdf_text(pdf_path)
    prompt = _build_ingest_prompt(prompt_path, text)

    payload = build_chat_payload(manual_model, prompt, _ingest_schema())
    if llm_mode == "api":
        if llm_config is None:
            raise ValueError("Missing LLM config for API mode")
        content = _request_llm_content(llm_config, prompt)
    elif llm_mode == "offline":
        if request_path is None or response_path is None:
            raise ValueError("Offline mode requires request/response paths")
        content = _manual_llm_content(
            payload=payload,
            request_path=request_path,
            response_path=response_path,
            base_url=manual_base_url,
        )
    else:
        raise ValueError(f"Unknown LLM mode: {llm_mode}")

    parsed = parse_ingest_response(content)
    return write_ingest_files(data_dir, parsed, overwrite=overwrite)


def parse_ingest_response(text: str) -> ParsedCv:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response must be valid JSON") from exc
    return parse_ingest_payload(payload)


def parse_ingest_payload(payload: object) -> ParsedCv:
    if not isinstance(payload, dict):
        raise ValueError("Ingest payload must be a JSON object")

    profile_raw = payload.get("profile")
    if not isinstance(profile_raw, dict):
        raise ValueError("Missing or invalid profile section")

    links = _parse_links(profile_raw.get("links"))
    profile = ParsedProfile(
        name=_coerce_str(profile_raw.get("name")),
        headline=_coerce_str(profile_raw.get("headline")),
        location=_coerce_str(profile_raw.get("location")),
        email=_coerce_str(profile_raw.get("email")),
        about_me=_coerce_str(profile_raw.get("about_me")),
        links=links,
    )

    experience = _parse_experience(payload.get("experience"))
    projects = _parse_projects(payload.get("projects"))
    skills = _parse_skills(payload.get("skills"))
    education = _parse_education(payload.get("education"))

    return ParsedCv(
        profile=profile,
        experience=experience,
        projects=projects,
        skills=skills,
        education=education,
    )


def write_ingest_files(data_dir: Path, parsed: ParsedCv, *, overwrite: bool) -> IngestResult:
    warnings: list[str] = []
    written: list[Path] = []
    data_dir.mkdir(parents=True, exist_ok=True)

    used_ids: set[str] = {"profile", "skills", "education"}

    profile_path = data_dir / "profile.md"
    _ensure_writable(profile_path, overwrite=overwrite)
    profile_frontmatter = {
        "id": "profile",
        "name": _require_field(parsed.profile.name, "profile.name", warnings),
        "headline": _require_field(parsed.profile.headline, "profile.headline", warnings),
        "location": _require_field(parsed.profile.location, "profile.location", warnings),
        "email": parsed.profile.email,
        "links": [
            {"label": _require_field(link.label, "profile.links.label", warnings), "url": link.url}
            for link in parsed.profile.links
            if link.label or link.url
        ],
        "about_me": _require_field(parsed.profile.about_me, "profile.about_me", warnings),
    }
    _write_frontmatter(profile_path, profile_frontmatter, note="Generated from PDF.")
    written.append(profile_path)

    skills_path = data_dir / "skills.md"
    _ensure_writable(skills_path, overwrite=overwrite)
    skills_frontmatter = {
        "id": "skills",
        "categories": [
            {
                "name": _require_field(cat.name, "skills.category.name", warnings),
                "items": list(cat.items),
            }
            for cat in parsed.skills
        ],
    }
    _write_frontmatter(skills_path, skills_frontmatter, note="Generated from PDF.")
    written.append(skills_path)

    education_path = data_dir / "education.md"
    _ensure_writable(education_path, overwrite=overwrite)
    education_frontmatter = {
        "id": "education",
        "entries": [
            {
                "institution": _require_field(entry.institution, "education.institution", warnings),
                "degree": _require_field(entry.degree, "education.degree", warnings),
                "location": entry.location,
                "start_date": entry.start_date,
                "end_date": entry.end_date,
            }
            for entry in parsed.education
        ],
    }
    _write_frontmatter(education_path, education_frontmatter, note="Generated from PDF.")
    written.append(education_path)

    experience_dir = data_dir / "experience"
    experience_dir.mkdir(parents=True, exist_ok=True)
    for idx, entry in enumerate(parsed.experience, start=1):
        exp_id = _unique_id(
            _slugify(f"exp_{entry.company or 'unknown'}_{entry.start_date or idx}"), used_ids
        )
        used_ids.add(exp_id)
        exp_path = experience_dir / f"{USER_PREFIX}{exp_id}.md"
        _ensure_writable(exp_path, overwrite=overwrite)
        exp_frontmatter = {
            "id": exp_id,
            "company": _require_field(entry.company, "experience.company", warnings),
            "title": _require_field(entry.title, "experience.title", warnings),
            "location": entry.location,
            "start_date": _require_field(entry.start_date, "experience.start_date", warnings),
            "end_date": entry.end_date,
            "tags": list(entry.tags),
            "bullets": list(entry.bullets),
        }
        _write_frontmatter(exp_path, exp_frontmatter, note="Generated from PDF.")
        written.append(exp_path)

    projects_dir = data_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    for idx, entry in enumerate(parsed.projects, start=1):
        proj_id = _unique_id(_slugify(f"proj_{entry.name or idx}"), used_ids)
        used_ids.add(proj_id)
        proj_path = projects_dir / f"{proj_id}.md"
        _ensure_writable(proj_path, overwrite=overwrite)
        proj_frontmatter = {
            "id": proj_id,
            "name": _require_field(entry.name, "projects.name", warnings),
            "company": entry.company,
            "role": entry.role,
            "start_date": entry.start_date,
            "end_date": entry.end_date,
            "tags": list(entry.tags),
            "bullets": list(entry.bullets),
        }
        _write_frontmatter(proj_path, proj_frontmatter, note="Generated from PDF.")
        written.append(proj_path)

    return IngestResult(written_paths=tuple(written), warnings=tuple(warnings))


def _build_ingest_prompt(path: Path, pdf_text: str) -> str:
    prompt = path.read_text(encoding="utf-8")
    return prompt.replace("{{PDF_TEXT}}", pdf_text.strip())


def _request_llm_content(config: LLMConfig, prompt: str) -> str:
    url = build_chat_endpoint(config.base_url)
    payload = build_chat_payload(config.model, prompt, _ingest_schema())
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    req = Request(url, data=data, headers=headers, method="POST")
    with urlopen(req, timeout=config.timeout_seconds) as resp:  # noqa: S310
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    content = extract_chat_content(parsed)
    if content is None:
        raise ValueError("Unexpected LLM response shape")
    return content


def _manual_llm_content(
    *,
    payload: dict[str, object],
    request_path: Path,
    response_path: Path,
    base_url: str | None,
) -> str:
    request_bundle: dict[str, Any] = {"payload": payload}
    if base_url:
        request_bundle["endpoint"] = build_chat_endpoint(base_url)
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(request_bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not response_path.exists():
        raise ValueError(
            "Manual LLM mode: response file missing. "
            f"Paste model output into {response_path} and retry."
        )
    raw = response_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    content = extract_chat_content(parsed)
    if content is not None:
        return content
    direct = parsed.get("content") if isinstance(parsed, dict) else None
    if isinstance(direct, str):
        return direct
    return raw


def _parse_links(value: object) -> tuple[ParsedLink, ...]:
    if not isinstance(value, list):
        return ()
    links: list[ParsedLink] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        links.append(
            ParsedLink(
                label=_coerce_str(item.get("label")),
                url=_coerce_str(item.get("url")),
            )
        )
    return tuple(links)


def _parse_experience(value: object) -> tuple[ParsedExperience, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedExperience] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(
            ParsedExperience(
                company=_coerce_str(item.get("company")),
                title=_coerce_str(item.get("title")),
                location=_coerce_str(item.get("location")),
                start_date=_coerce_str(item.get("start_date")),
                end_date=_coerce_str(item.get("end_date")),
                bullets=_coerce_str_list(item.get("bullets")),
                tags=_coerce_str_list(item.get("tags")),
            )
        )
    return tuple(items)


def _parse_projects(value: object) -> tuple[ParsedProject, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedProject] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(
            ParsedProject(
                name=_coerce_str(item.get("name")),
                company=_coerce_str(item.get("company")),
                role=_coerce_str(item.get("role")),
                start_date=_coerce_str(item.get("start_date")),
                end_date=_coerce_str(item.get("end_date")),
                bullets=_coerce_str_list(item.get("bullets")),
                tags=_coerce_str_list(item.get("tags")),
            )
        )
    return tuple(items)


def _parse_skills(value: object) -> tuple[ParsedSkillCategory, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedSkillCategory] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(
            ParsedSkillCategory(
                name=_coerce_str(item.get("name")),
                items=_coerce_str_list(item.get("items")),
            )
        )
    return tuple(items)


def _parse_education(value: object) -> tuple[ParsedEducation, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedEducation] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(
            ParsedEducation(
                institution=_coerce_str(item.get("institution")),
                degree=_coerce_str(item.get("degree")),
                location=_coerce_str(item.get("location")),
                start_date=_coerce_str(item.get("start_date")),
                end_date=_coerce_str(item.get("end_date")),
            )
        )
    return tuple(items)


def _coerce_str(value: object) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return None


def _coerce_str_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if text:
            items.append(text)
    return tuple(items)


def _require_field(value: str | None, field: str, warnings: list[str]) -> str:
    if value:
        return value
    warnings.append(f"Missing {field}; set placeholder.")
    return _PLACEHOLDER


def _write_frontmatter(path: Path, frontmatter: dict[str, Any], note: str) -> None:
    content = "---\n"
    content += yaml.safe_dump(frontmatter, sort_keys=False).strip()
    content += "\n---\n\n"
    content += "Notes (not rendered):\n"
    content += f"- {note}\n"
    path.write_text(content, encoding="utf-8")


def _ensure_writable(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(f"Refusing to overwrite existing file: {path}")


def _slugify(text: str) -> str:
    slug = _SAFE_ID_RE.sub("_", text.strip().lower()).strip("_")
    return slug or "item"


def _unique_id(base: str, used: set[str]) -> str:
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def _ingest_schema() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "pdf_ingest_response",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["profile", "experience", "projects", "skills", "education"],
                "properties": {
                    "profile": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "headline",
                            "location",
                            "email",
                            "links",
                            "about_me",
                        ],
                        "properties": {
                            "name": {"type": "string"},
                            "headline": {"type": "string"},
                            "location": {"type": "string"},
                            "email": {"type": "string"},
                            "links": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["label", "url"],
                                    "properties": {
                                        "label": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                },
                            },
                            "about_me": {"type": "string"},
                        },
                    },
                    "experience": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "company",
                                "title",
                                "location",
                                "start_date",
                                "end_date",
                                "bullets",
                                "tags",
                            ],
                            "properties": {
                                "company": {"type": "string"},
                                "title": {"type": "string"},
                                "location": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                                "bullets": {"type": "array", "items": {"type": "string"}},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "name",
                                "company",
                                "role",
                                "start_date",
                                "end_date",
                                "bullets",
                                "tags",
                            ],
                            "properties": {
                                "name": {"type": "string"},
                                "company": {"type": "string"},
                                "role": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                                "bullets": {"type": "array", "items": {"type": "string"}},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "skills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "items"],
                            "properties": {
                                "name": {"type": "string"},
                                "items": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "institution",
                                "degree",
                                "location",
                                "start_date",
                                "end_date",
                            ],
                            "properties": {
                                "institution": {"type": "string"},
                                "degree": {"type": "string"},
                                "location": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }
