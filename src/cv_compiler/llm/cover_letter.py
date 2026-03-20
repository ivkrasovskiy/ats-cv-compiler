"""
LLM helpers for generating a cover letter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cv_compiler.llm._json_response import make_json_schema, parse_json_field
from cv_compiler.schema.models import ExperienceEntry, JobSpec, Profile


def build_cover_letter_prompt(
    prompt_path: Path,
    *,
    profile: Profile,
    experience: tuple[ExperienceEntry, ...],
    job: JobSpec,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    profile_payload: dict[str, Any] = {
        "name": profile.name,
        "headline": profile.headline,
        "location": profile.location,
        "about_me": profile.about_me,
    }
    if profile.email:
        profile_payload["email"] = profile.email
    experience_payload = [
        {
            "id": e.id,
            "company": e.company,
            "title": e.title,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "tags": list(e.tags),
            "bullets": list(e.bullets),
        }
        for e in experience
    ]
    job_payload: dict[str, Any] = {
        "id": job.id,
        "title": job.title,
        "raw_text": job.raw_text,
        "keywords": list(job.keywords),
    }
    prompt = prompt.replace("{{PROFILE}}", yaml.safe_dump(profile_payload, sort_keys=False).strip())
    prompt = prompt.replace(
        "{{EXPERIENCE}}", yaml.safe_dump(experience_payload, sort_keys=False).strip()
    )
    prompt = prompt.replace("{{JOB}}", yaml.safe_dump(job_payload, sort_keys=False).strip())
    prompt = prompt.replace("{{JOB_CONTEXT}}", "")
    return prompt


def parse_cover_letter(text: str) -> str:
    return parse_json_field(text, field="cover_letter", label="Cover letter")


def cover_letter_schema() -> dict[str, object]:
    return make_json_schema("cover_letter_response", "cover_letter")
