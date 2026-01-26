"""
OpenAI-compatible LLM provider (chat-completions).

Uses an HTTP endpoint specified by LLMConfig. This provider is optional and only invoked when
`--llm openai` is set and config is available.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Sequence
from pathlib import Path
from urllib.request import Request, urlopen

from cv_compiler.llm.base import (
    BulletRewriteRequest,
    BulletRewriteResult,
    ExperienceDraft,
    LLMProvider,
)
from cv_compiler.llm.config import LLMConfig
from cv_compiler.llm.experience import (
    build_experience_prompt,
    load_experience_templates,
    parse_experience_drafts,
)
from cv_compiler.llm.summary import (
    build_experience_summary_prompt,
    experience_summary_schema,
    parse_experience_summary,
)
from cv_compiler.llm.skills import (
    build_skills_prompt,
    parse_skill_highlights,
    skills_highlight_schema,
)
from cv_compiler.schema.models import JobSpec, Profile, ProjectEntry


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        config: LLMConfig,
        *,
        prompt_path: Path = Path("prompts/experience_prompt.md"),
        templates_path: Path = Path("prompts/experience_templates.yaml"),
        skills_prompt_path: Path = Path("prompts/skills_highlight_prompt.md"),
    ) -> None:
        self._config = config
        self._prompt_path = prompt_path
        self._templates_path = templates_path
        self._skills_prompt_path = skills_prompt_path

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]:
        _ = (items, instructions)
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
        content = request_chat_completion(
            self._config,
            prompt,
            response_format=experience_response_schema(),
        )
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
        content = request_chat_completion(
            self._config,
            prompt,
            response_format=skills_highlight_schema(),
        )
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
        payload = build_chat_payload(self._config.model, prompt, experience_summary_schema())
        content = _request_llm_content(self._config, payload)
        return parse_experience_summary(content)


def request_chat_completion(
    config: LLMConfig, prompt: str, response_format: dict[str, object] | None
) -> str:
    url = build_chat_endpoint(config.base_url)
    payload = build_chat_payload(config.model, prompt, response_format)
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


def build_chat_endpoint(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def build_chat_payload(
    model: str,
    prompt: str,
    response_format: dict[str, object] | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


def extract_chat_content(parsed: object) -> str | None:
    if not isinstance(parsed, dict):
        return None
    try:
        return parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None


def experience_response_schema() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "experience_response",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["experiences"],
                "properties": {
                    "experiences": {
                        "type": "array",
                        "maxItems": 5,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["id", "role", "source_project_ids", "bullets"],
                            "properties": {
                                "id": {"type": "string"},
                                "role": {"type": ["string", "null"]},
                                "keywords": {
                                    "type": "array",
                                    "maxItems": 8,
                                    "items": {"type": "string"},
                                },
                                "source_project_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "bullets": {
                                    "type": "array",
                                    "maxItems": 3,
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    }
                },
            },
        },
    }
