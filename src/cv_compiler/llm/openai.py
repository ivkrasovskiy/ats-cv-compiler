"""
OpenAI-compatible LLM provider (chat-completions).

Uses an HTTP endpoint specified by LLMConfig. This provider is optional and only invoked when
`--llm openai` is set and config is available.
"""

from __future__ import annotations

import json
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
from cv_compiler.schema.models import JobSpec, ProjectEntry


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        config: LLMConfig,
        *,
        prompt_path: Path = Path("prompts/experience_prompt.md"),
        templates_path: Path = Path("prompts/experience_templates.yaml"),
    ) -> None:
        self._config = config
        self._prompt_path = prompt_path
        self._templates_path = templates_path

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
        content = _chat_completion(self._config, prompt)
        return parse_experience_drafts(content)


def _chat_completion(config: LLMConfig, prompt: str) -> str:
    url = config.base_url.rstrip("/")
    if url.endswith("/v1"):
        url = f"{url}/chat/completions"
    else:
        url = f"{url}/v1/chat/completions"

    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    req = Request(url, data=data, headers=headers, method="POST")
    with urlopen(req, timeout=config.timeout_seconds) as resp:  # noqa: S310
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    try:
        return parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected LLM response shape") from exc
