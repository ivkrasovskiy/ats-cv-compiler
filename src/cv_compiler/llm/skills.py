"""
LLM helpers for highlighting skills/tools.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cv_compiler.schema.models import JobSpec, Profile

_MAX_HIGHLIGHTS = 5


@dataclass(frozen=True, slots=True)
class SkillHighlightRequest:
    skills: tuple[str, ...]
    profile_headline: str
    job: JobSpec | None


def build_skills_prompt(
    prompt_path: Path,
    *,
    skills: tuple[str, ...],
    profile: Profile,
    job: JobSpec | None,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt = prompt.replace("{{PROFILE_HEADLINE}}", profile.headline)
    job_payload: dict[str, Any] = {}
    if job is not None:
        job_payload = {
            "id": job.id,
            "title": job.title,
            "raw_text": job.raw_text,
            "keywords": list(job.keywords),
        }
    prompt = prompt.replace("{{JOB}}", yaml.safe_dump(job_payload, sort_keys=False).strip())
    prompt = prompt.replace("{{SKILLS}}", yaml.safe_dump(list(skills), sort_keys=False).strip())
    return prompt


def parse_skill_highlights(text: str, *, allowed_skills: tuple[str, ...]) -> tuple[str, ...]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM skill highlight response must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("LLM skill highlight response must be a JSON object")
    raw = data.get("highlighted_skills")
    if not isinstance(raw, list):
        raise ValueError("highlighted_skills must be a list")

    allowed_map = {s.strip().lower(): s for s in allowed_skills if s.strip()}
    highlights: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError("highlighted_skills items must be strings")
        key = item.strip().lower()
        if not key:
            continue
        if key not in allowed_map:
            raise ValueError(f"Unknown skill selected: {item}")
        value = allowed_map[key]
        if value not in highlights:
            highlights.append(value)
        if len(highlights) >= _MAX_HIGHLIGHTS:
            break
    return tuple(highlights)


def skills_highlight_schema() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "skills_highlight_response",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["highlighted_skills"],
                "properties": {
                    "highlighted_skills": {
                        "type": "array",
                        "maxItems": _MAX_HIGHLIGHTS,
                        "items": {"type": "string"},
                    }
                },
            },
        },
    }
