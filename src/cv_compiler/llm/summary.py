"""
LLM helpers for generating an experience summary paragraph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cv_compiler.schema.models import JobSpec, ProjectEntry


@dataclass(frozen=True, slots=True)
class ExperienceSummaryRequest:
    projects: tuple[ProjectEntry, ...]
    job: JobSpec | None


def build_experience_summary_prompt(
    prompt_path: Path,
    *,
    projects: tuple[ProjectEntry, ...],
    job: JobSpec | None,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
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
        "{{PROJECTS}}", yaml.safe_dump(project_payload, sort_keys=False).strip()
    )
    prompt = prompt.replace("{{JOB}}", yaml.safe_dump(job_payload, sort_keys=False).strip())
    return prompt


def parse_experience_summary(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Experience summary must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("Experience summary response must be a JSON object")
    value = data.get("summary")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Experience summary must include a non-empty summary field")
    return value.strip()


def experience_summary_schema() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "experience_summary_response",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["summary"],
                "properties": {
                    "summary": {"type": "string"},
                },
            },
        },
    }
