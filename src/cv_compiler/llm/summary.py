"""
LLM helpers for generating an experience summary paragraph.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cv_compiler.llm._json_response import make_json_schema, parse_json_field
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
    prompt = prompt.replace("{{JOB_CONTEXT}}", "")
    return prompt


def parse_experience_summary(text: str) -> str:
    return parse_json_field(text, field="summary", label="Experience summary")


def experience_summary_schema() -> dict[str, object]:
    return make_json_schema("experience_summary_response", "summary")
