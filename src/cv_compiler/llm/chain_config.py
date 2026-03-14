"""
Agent chain configuration for the multi-agent CV pipeline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.llm.config import read_env_file


@dataclass(frozen=True, slots=True)
class AgentChainConfig:
    codex: CodexExecConfig
    context_dir: Path
    timeout_job_analysis: int
    timeout_experience: int
    timeout_skills: int
    timeout_bullet_polish: int
    timeout_summary: int
    keyword_coverage_min: float
    max_bullet_chars: int
    max_summary_chars: int
    enabled: bool

    @staticmethod
    def from_env(
        *,
        env_path: Path | None = Path("config/llm.env"),
    ) -> AgentChainConfig:
        file_values = read_env_file(env_path) if env_path else {}

        def _get(key: str, default: str) -> str:
            return os.getenv(key) or file_values.get(key) or default

        codex = CodexExecConfig.from_env(env_path=env_path)
        context_dir = Path(_get("CV_AGENT_CONTEXT_DIR", "out/context"))
        timeout_job_analysis = int(_get("CV_AGENT_TIMEOUT_JOB_ANALYSIS", "120"))
        timeout_experience = int(_get("CV_AGENT_TIMEOUT_EXPERIENCE", "600"))
        timeout_skills = int(_get("CV_AGENT_TIMEOUT_SKILLS", "120"))
        timeout_bullet_polish = int(_get("CV_AGENT_TIMEOUT_BULLET_POLISH", "180"))
        timeout_summary = int(_get("CV_AGENT_TIMEOUT_SUMMARY", "180"))
        keyword_coverage_min = float(_get("CV_AGENT_KEYWORD_COVERAGE_MIN", "0.5"))
        max_bullet_chars = int(_get("CV_AGENT_MAX_BULLET_CHARS", "200"))
        max_summary_chars = int(_get("CV_AGENT_MAX_SUMMARY_CHARS", "1500"))
        enabled_raw = _get("CV_AGENT_CHAIN_ENABLED", "false")
        enabled = enabled_raw.strip().lower() in {"1", "true", "yes", "on"}

        return AgentChainConfig(
            codex=codex,
            context_dir=context_dir,
            timeout_job_analysis=timeout_job_analysis,
            timeout_experience=timeout_experience,
            timeout_skills=timeout_skills,
            timeout_bullet_polish=timeout_bullet_polish,
            timeout_summary=timeout_summary,
            keyword_coverage_min=keyword_coverage_min,
            max_bullet_chars=max_bullet_chars,
            max_summary_chars=max_summary_chars,
            enabled=enabled,
        )
