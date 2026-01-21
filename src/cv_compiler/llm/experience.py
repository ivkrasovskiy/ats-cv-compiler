"""
Helpers for LLM-derived experience generation.

This module builds prompts, validates LLM responses, and writes generated experience artifacts.
"""

from __future__ import annotations

import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cv_compiler.llm.base import ExperienceDraft
from cv_compiler.schema.models import JobSpec, ProjectEntry

LLM_PREFIX = "llm_"
USER_PREFIX = "user_"

_NUM_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?%?")
_SAFE_ID_RE = re.compile(r"[^a-z0-9_]+")
_ACTIVE_USER_RE = re.compile(r"^user_[a-z0-9_]+$")
_ACTIVE_LLM_RE = re.compile(r"^llm_[a-z0-9_]+$")
_THINK_RE = re.compile(r"<think>.*?</think>", re.S)
_YAML_START_RE = re.compile(r"(?m)^\s*experiences\s*:\s*$")


@dataclass(frozen=True, slots=True)
class ExperienceTemplate:
    id: str
    template: str


def load_experience_templates(path: Path) -> tuple[ExperienceTemplate, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Templates must be a list: {path}")
    out: list[ExperienceTemplate] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid template entry: {item!r}")
        template_id = item.get("id")
        template_text = item.get("template")
        if not isinstance(template_id, str) or not isinstance(template_text, str):
            raise ValueError(f"Template entries must have id/template strings: {item!r}")
        out.append(ExperienceTemplate(id=template_id, template=template_text))
    return tuple(out)


def build_experience_prompt(
    prompt_path: Path,
    *,
    templates: tuple[ExperienceTemplate, ...],
    projects: tuple[ProjectEntry, ...],
    job: JobSpec | None,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    template_payload = [{"id": t.id, "template": t.template} for t in templates]
    project_payload = [
        {
            "id": p.id,
            "name": p.name,
            "company": p.company,
            "role": p.role,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "tags": list(p.tags),
            "bullets": list(p.bullets),
        }
        for p in projects
    ]
    job_payload: dict[str, Any] = {}
    if job is not None:
        job_payload = {
            "id": job.id,
            "title": job.title,
            "raw_text": job.raw_text,
            "keywords": list(job.keywords),
        }

    prompt = prompt.replace(
        "{{TEMPLATES}}", yaml.safe_dump(template_payload, sort_keys=False).strip()
    )
    prompt = prompt.replace(
        "{{PROJECTS}}", yaml.safe_dump(project_payload, sort_keys=False).strip()
    )
    prompt = prompt.replace("{{JOB}}", yaml.safe_dump(job_payload, sort_keys=False).strip())
    return prompt


def parse_experience_drafts(text: str) -> tuple[ExperienceDraft, ...]:
    cleaned = _extract_yaml_payload(text)
    data = yaml.safe_load(cleaned)
    if not isinstance(data, dict) or "experiences" not in data:
        raise ValueError("LLM response must be YAML with an `experiences` list")
    raw_exps = data["experiences"]
    if not isinstance(raw_exps, list):
        raise ValueError("`experiences` must be a list")
    drafts: list[ExperienceDraft] = []
    for raw in raw_exps:
        if not isinstance(raw, dict):
            raise ValueError("Each experience must be a mapping")
        exp_id = raw.get("id")
        role = raw.get("role")
        source_ids = raw.get("source_project_ids")
        bullets = raw.get("bullets")
        if not isinstance(exp_id, str) or not exp_id.strip():
            raise ValueError("Experience id must be a non-empty string")
        if role is not None and not isinstance(role, str):
            raise ValueError("Experience role must be a string or null")
        if not isinstance(source_ids, list) or not all(isinstance(x, str) for x in source_ids):
            raise ValueError("source_project_ids must be a list of strings")
        if not isinstance(bullets, list) or not all(isinstance(x, str) for x in bullets):
            raise ValueError("bullets must be a list of strings")
        drafts.append(
            ExperienceDraft(
                id=_safe_id(exp_id),
                role=role.strip() if isinstance(role, str) and role.strip() else None,
                bullets=tuple(b.strip() for b in bullets if b.strip()),
                source_project_ids=tuple(x.strip() for x in source_ids if x.strip()),
            )
        )
    return tuple(drafts)


def write_experience_artifacts(
    data_dir: Path,
    *,
    projects: tuple[ProjectEntry, ...],
    drafts: tuple[ExperienceDraft, ...],
) -> tuple[Path, ...]:
    if len(drafts) > 5:
        raise ValueError("LLM must produce at most 5 experiences")

    project_by_id = {p.id: p for p in projects}
    allowed_numbers = _collect_allowed_numbers(projects)

    experience_dir = data_dir / "experience"
    experience_dir.mkdir(parents=True, exist_ok=True)

    used_ids: set[str] = set()
    written: list[Path] = []
    for draft in drafts:
        if not draft.source_project_ids:
            raise ValueError(f"Experience {draft.id} has no source_project_ids")
        src_projects = []
        for pid in draft.source_project_ids:
            if pid not in project_by_id:
                raise ValueError(f"Unknown project id {pid} in experience {draft.id}")
            src_projects.append(project_by_id[pid])

        company_set = {p.company for p in src_projects if p.company}
        if len(company_set) != 1:
            raise ValueError(f"Experience {draft.id} must reference projects with a single company")
        company = next(iter(company_set))

        start_dates = [p.start_date for p in src_projects if p.start_date]
        if not start_dates:
            raise ValueError(f"Experience {draft.id} requires project start_date values")
        end_dates = [p.end_date for p in src_projects if p.end_date]
        start_date = min(start_dates)
        end_date = max(end_dates) if end_dates else None

        role_set = {p.role for p in src_projects if p.role}
        role = None
        if len(role_set) == 1:
            role = next(iter(role_set))
        elif draft.role:
            if draft.role in role_set:
                role = draft.role
        if role is None:
            raise ValueError(f"Experience {draft.id} needs a role from project data")

        tags = sorted({t for p in src_projects for t in p.tags})
        bullets = tuple(_validate_bullet_numbers(b, allowed_numbers) for b in draft.bullets[:3])
        exp_id = _derive_experience_id(company, start_date, used_ids)

        frontmatter = {
            "id": exp_id,
            "company": company,
            "title": role,
            "location": None,
            "start_date": start_date,
            "end_date": end_date,
            "tags": tags,
            "bullets": list(bullets),
            "source_project_ids": list(draft.source_project_ids),
        }

        content = "---\n"
        content += yaml.safe_dump(frontmatter, sort_keys=False).strip()
        content += "\n---\n"

        out_path = experience_dir / f"{LLM_PREFIX}{exp_id}.md"
        out_path.write_text(content, encoding="utf-8")
        written.append(out_path)

    return tuple(written)


def archive_user_experience_files(data_dir: Path) -> tuple[Path, ...]:
    experience_dir = data_dir / "experience"
    if not experience_dir.exists():
        return ()
    ts = int(time.time())
    archived: list[Path] = []
    for path in experience_dir.glob("*.md"):
        stem = path.stem
        if not _ACTIVE_USER_RE.match(stem):
            continue
        dest = experience_dir / f"{stem}.{ts}.md"
        counter = 1
        while dest.exists():
            dest = experience_dir / f"{stem}.{ts}_{counter}.md"
            counter += 1
        path.rename(dest)
        archived.append(dest)
    return tuple(archived)


def backup_llm_experience_files(data_dir: Path) -> Path | None:
    experience_dir = data_dir / "experience"
    if not experience_dir.exists():
        return None
    candidates = [
        path for path in experience_dir.glob("*.md") if _ACTIVE_LLM_RE.match(path.stem)
    ]
    if not candidates:
        return None
    backup_root = data_dir.parent / "tmp"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_root / f"llm_experience_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    for path in candidates:
        shutil.move(path, backup_dir / path.name)
    return backup_dir


def restore_llm_experience_files(backup_dir: Path, data_dir: Path) -> None:
    if not backup_dir.exists():
        return
    experience_dir = data_dir / "experience"
    experience_dir.mkdir(parents=True, exist_ok=True)
    for path in backup_dir.glob("*.md"):
        dest = experience_dir / path.name
        if dest.exists():
            dest.unlink()
        shutil.move(path, dest)
    shutil.rmtree(backup_dir, ignore_errors=True)


def _collect_allowed_numbers(projects: tuple[ProjectEntry, ...]) -> set[str]:
    tokens: set[str] = set()
    for p in projects:
        text_values: list[str] = [p.name, *p.bullets]
        if p.company:
            text_values.append(p.company)
        if p.role:
            text_values.append(p.role)
        if p.start_date:
            text_values.append(p.start_date)
        if p.end_date:
            text_values.append(p.end_date)
        text_values.extend(p.tags)
        for text in text_values:
            tokens.update(_NUM_TOKEN_RE.findall(text))
    return tokens


def _validate_bullet_numbers(bullet: str, allowed_numbers: set[str]) -> str:
    for token in _NUM_TOKEN_RE.findall(bullet):
        if token not in allowed_numbers:
            raise ValueError(f"Unknown numeric token {token!r} in bullet: {bullet}")
    return bullet


def _safe_id(text: str) -> str:
    slug = _SAFE_ID_RE.sub("_", text.strip().lower()).strip("_")
    if not slug:
        raise ValueError("Experience id cannot be empty after sanitization")
    return slug


def _derive_experience_id(company: str, start_date: str, used_ids: set[str]) -> str:
    base = _safe_id(f"exp_{company}_{start_date}")
    candidate = base
    counter = 2
    while candidate in used_ids:
        candidate = f"{base}_{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1])
    return text


def _extract_yaml_payload(text: str) -> str:
    stripped = _THINK_RE.sub("", text.strip()).strip()
    if "```" in stripped:
        parts = stripped.split("```")
        for i in range(1, len(parts), 2):
            block = _strip_fence_language(parts[i])
            if "experiences:" in block:
                return block.strip()
    match = _YAML_START_RE.search(stripped)
    if match:
        return stripped[match.start() :].strip()
    return _strip_code_fence(stripped).strip()


def _strip_fence_language(block: str) -> str:
    lines = block.splitlines()
    if lines and lines[0].strip().lower() in {"yaml", "yml"}:
        return "\n".join(lines[1:])
    return block
