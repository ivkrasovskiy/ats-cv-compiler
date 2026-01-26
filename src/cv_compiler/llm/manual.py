"""
Manual/offline LLM provider.

Writes an OpenAI-compatible request payload to disk and reads a user-supplied response file.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from cv_compiler.llm.base import (
    BulletRewriteRequest,
    BulletRewriteResult,
    ExperienceDraft,
    LLMProvider,
)
from cv_compiler.llm.experience import (
    build_experience_prompt,
    load_experience_templates,
    parse_experience_drafts,
)
from cv_compiler.llm.openai import (
    build_chat_endpoint,
    build_chat_payload,
    experience_response_schema,
    extract_chat_content,
)
from cv_compiler.llm.skills import (
    build_skills_prompt,
    parse_skill_highlights,
    skills_highlight_schema,
)
from cv_compiler.llm.summary import (
    build_experience_summary_prompt,
    experience_summary_schema,
    parse_experience_summary,
)
from cv_compiler.schema.models import JobSpec, Profile, ProjectEntry


class ManualProvider(LLMProvider):
    name = "manual"

    def __init__(
        self,
        *,
        request_path: Path,
        response_path: Path,
        skills_request_path: Path,
        skills_response_path: Path,
        model: str = "manual",
        base_url: str | None = None,
        prompt_path: Path = Path("prompts/experience_prompt.md"),
        templates_path: Path = Path("prompts/experience_templates.yaml"),
        skills_prompt_path: Path = Path("prompts/skills_highlight_prompt.md"),
    ) -> None:
        self._request_path = request_path
        self._response_path = response_path
        self._skills_request_path = skills_request_path
        self._skills_response_path = skills_response_path
        self._model = model
        self._base_url = base_url
        self._prompt_path = prompt_path
        self._templates_path = templates_path
        self._skills_prompt_path = skills_prompt_path

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]:
        _ = instructions
        return [BulletRewriteResult(item_id=item.item_id, bullets=item.bullets) for item in items]

    def generate_experience(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> Sequence[ExperienceDraft]:
        templates = load_experience_templates(self._templates_path)
        prompt = build_experience_prompt(
            self._prompt_path,
            templates=templates,
            projects=tuple(projects),
            job=job,
        )
        payload = build_chat_payload(self._model, prompt, experience_response_schema())
        request_bundle = {"payload": payload}
        if self._base_url:
            request_bundle["endpoint"] = build_chat_endpoint(self._base_url)
        self._request_path.parent.mkdir(parents=True, exist_ok=True)
        self._request_path.write_text(
            json.dumps(request_bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if not self._response_path.exists():
            raise ValueError(
                "Manual LLM mode: response file missing. "
                f"Paste model output into {self._response_path} and retry."
            )
        raw = self._response_path.read_text(encoding="utf-8")
        content = _extract_response_content(raw)
        return parse_experience_drafts(content)

    def highlight_skills(
        self,
        skills: Sequence[str],
        profile: Profile,
        job: JobSpec | None,
    ) -> Sequence[str]:
        prompt = build_skills_prompt(
            self._skills_prompt_path,
            skills=tuple(skills),
            profile=profile,
            job=job,
        )
        payload = build_chat_payload(self._model, prompt, skills_highlight_schema())
        request_bundle = {"payload": payload}
        if self._base_url:
            request_bundle["endpoint"] = build_chat_endpoint(self._base_url)
        self._skills_request_path.parent.mkdir(parents=True, exist_ok=True)
        self._skills_request_path.write_text(
            json.dumps(request_bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if not self._skills_response_path.exists():
            raise ValueError(
                "Manual LLM mode: response file missing. "
                f"Paste model output into {self._skills_response_path} and retry."
            )
        raw = self._skills_response_path.read_text(encoding="utf-8")
        content = _extract_response_content(raw)
        return parse_skill_highlights(content, allowed_skills=tuple(skills))

    def generate_experience_summary(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> str:
        prompt = build_experience_summary_prompt(
            Path("prompts/experience_summary_prompt.md"),
            projects=tuple(projects),
            job=job,
        )
        payload = build_chat_payload(self._model, prompt, experience_summary_schema())
        request_bundle = {"payload": payload}
        if self._base_url:
            request_bundle["endpoint"] = build_chat_endpoint(self._base_url)
        summary_request_path = self._request_path.with_name("llm_summary_request.json")
        summary_response_path = self._response_path.with_name("llm_summary_response.json")
        summary_request_path.parent.mkdir(parents=True, exist_ok=True)
        summary_request_path.write_text(
            json.dumps(request_bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not summary_response_path.exists():
            raise ValueError(
                "Manual LLM mode: summary response file missing. "
                f"Paste model output into {summary_response_path} and retry."
            )
        raw = summary_response_path.read_text(encoding="utf-8")
        content = _extract_response_content(raw)
        return parse_experience_summary(content)


def _extract_response_content(raw: str) -> str:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    content = extract_chat_content(parsed)
    if content is not None:
        return content
    if isinstance(parsed, dict):
        direct = parsed.get("content")
        if isinstance(direct, str):
            return direct
    return raw
