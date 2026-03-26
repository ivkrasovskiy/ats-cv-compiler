"""
Unified AI provider resolver.

Reads CV_AI_PROVIDER from config/llm.env and returns a ResolvedProvider that
tells callers whether to use the API path (LLMConfig) or CLI path (CodexExecConfig).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.llm.config import LLMConfig, read_env_file


@dataclass(frozen=True, slots=True)
class ResolvedProvider:
    ingest_mode: str  # "api" | "cli"
    llm_config: LLMConfig | None
    codex_config: CodexExecConfig | None


def resolve_from_env(env_path: Path = Path("config/llm.env")) -> ResolvedProvider:
    """Resolve AI provider from CV_AI_PROVIDER env var or config file."""
    import os

    file_values = read_env_file(env_path) if env_path.exists() else {}
    provider = os.getenv("CV_AI_PROVIDER") or file_values.get("CV_AI_PROVIDER") or "gemini"
    provider = provider.strip().lower()

    if provider == "gemini":
        gemini_model = (
            os.getenv("CV_GEMINI_MODEL")
            or file_values.get("CV_GEMINI_MODEL")
            or "gemini-2.0-flash"
        )
        return ResolvedProvider(
            ingest_mode="cli",
            llm_config=None,
            codex_config=CodexExecConfig(
                command="gemini",
                args=("-p", ""),
                model=gemini_model,
                timeout_seconds=300,
                prompt_mode="stdin",
                progress=False,
            ),
        )

    if provider == "claude":
        return ResolvedProvider(
            ingest_mode="cli",
            llm_config=None,
            codex_config=CodexExecConfig(
                command="claude",
                args=("-p",),
                model=None,
                timeout_seconds=300,
                prompt_mode="stdin",
                progress=False,
            ),
        )

    # "custom" or anything else → API path
    return ResolvedProvider(
        ingest_mode="api",
        llm_config=LLMConfig.from_env(env_path=env_path),
        codex_config=None,
    )
