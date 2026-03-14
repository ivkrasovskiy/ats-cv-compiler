"""
JobAnalysis dataclass and helpers for the agent chain context file.

Agent 1 writes out/context/job_analysis.yaml; Agents 2-5 read it via load_job_analysis().
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class JobAnalysis:
    job_title: str
    seniority_level: str
    required_skills: tuple[str, ...]
    implied_skills: tuple[str, ...]
    key_themes: tuple[str, ...]
    must_have_experiences: tuple[str, ...]
    nice_to_have_experiences: tuple[str, ...]
    tone_keywords: tuple[str, ...]


_VALID_SENIORITY = frozenset({"junior", "mid", "senior", "staff", "lead"})
_CONTEXT_FILENAME = "job_analysis.yaml"


def parse_job_analysis(raw: str) -> JobAnalysis:
    """Parse YAML text (from LLM output) into a JobAnalysis. Raises ValueError on invalid input."""
    text = raw.strip()
    # Strip code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1])

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Job analysis must be a YAML mapping")

    def _str_list(key: str) -> tuple[str, ...]:
        val = data.get(key) or []
        if not isinstance(val, list):
            raise ValueError(f"'{key}' must be a list in job analysis")
        return tuple(str(x).strip() for x in val if str(x).strip())

    job_title = str(data.get("job_title") or "").strip()
    if not job_title:
        raise ValueError("job_analysis: missing 'job_title'")

    seniority_level = str(data.get("seniority_level") or "mid").strip().lower()
    if seniority_level not in _VALID_SENIORITY:
        warnings.warn(
            f"job_analysis: unknown seniority_level {seniority_level!r}; defaulting to 'mid'",
            stacklevel=2,
        )
        seniority_level = "mid"

    return JobAnalysis(
        job_title=job_title,
        seniority_level=seniority_level,
        required_skills=_str_list("required_skills"),
        implied_skills=_str_list("implied_skills"),
        key_themes=_str_list("key_themes"),
        must_have_experiences=_str_list("must_have_experiences"),
        nice_to_have_experiences=_str_list("nice_to_have_experiences"),
        tone_keywords=_str_list("tone_keywords"),
    )


def write_job_analysis(analysis: JobAnalysis, context_dir: Path) -> Path:
    """Serialize and write job_analysis.yaml to context_dir. Returns the written path."""
    context_dir.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "job_title": analysis.job_title,
        "seniority_level": analysis.seniority_level,
        "required_skills": list(analysis.required_skills),
        "implied_skills": list(analysis.implied_skills),
        "key_themes": list(analysis.key_themes),
        "must_have_experiences": list(analysis.must_have_experiences),
        "nice_to_have_experiences": list(analysis.nice_to_have_experiences),
        "tone_keywords": list(analysis.tone_keywords),
    }
    out_path = context_dir / _CONTEXT_FILENAME
    out_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return out_path


def load_job_analysis(context_dir: Path) -> JobAnalysis | None:
    """Load job_analysis.yaml from context_dir. Returns None if file does not exist."""
    path = context_dir / _CONTEXT_FILENAME
    if not path.exists():
        return None
    return parse_job_analysis(path.read_text(encoding="utf-8"))


def format_job_analysis_context(analysis: JobAnalysis) -> str:
    """Format JobAnalysis as a readable block for injection into downstream prompts."""
    lines = [
        f"Job Title: {analysis.job_title}",
        f"Seniority: {analysis.seniority_level}",
    ]
    if analysis.required_skills:
        lines.append("Required Skills: " + ", ".join(analysis.required_skills))
    if analysis.implied_skills:
        lines.append("Implied Skills: " + ", ".join(analysis.implied_skills))
    if analysis.key_themes:
        lines.append("Key Themes: " + ", ".join(analysis.key_themes))
    if analysis.must_have_experiences:
        lines.append("Must-Have Experiences: " + "; ".join(analysis.must_have_experiences))
    if analysis.nice_to_have_experiences:
        lines.append("Nice-to-Have Experiences: " + "; ".join(analysis.nice_to_have_experiences))
    if analysis.tone_keywords:
        lines.append("Tone: " + ", ".join(analysis.tone_keywords))
    return "\n".join(lines)
