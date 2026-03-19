"""
Multi-agent chain provider for the CV compiler.

Runs a 5-agent pipeline using `claude -p` (Claude Code subscription), chaining agents via
a shared context file at out/context/job_analysis.yaml.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import yaml

from cv_compiler.llm.base import (
    BulletRewriteRequest,
    BulletRewriteResult,
    ExperienceDraft,
)
from cv_compiler.llm.bullet_polish import build_bullet_polish_prompt, parse_bullet_polish_response
from cv_compiler.llm.chain_config import AgentChainConfig
from cv_compiler.llm.codex import _extract_json_payload
from cv_compiler.llm.experience import (
    build_experience_prompt,
    load_experience_templates,
    parse_experience_drafts,
)
from cv_compiler.llm.job_analysis import (
    JobAnalysis,
    format_job_analysis_context,
    load_job_analysis,
    parse_job_analysis,
    write_job_analysis,
)
from cv_compiler.llm.skills import (
    build_skills_prompt,
    build_skills_select_prompt,
    parse_skill_highlights,
    parse_skill_selection,
)
from cv_compiler.llm.summary import build_experience_summary_prompt, parse_experience_summary
from cv_compiler.schema.models import JobSpec, Profile, ProjectEntry

_JOB_ANALYSIS_PROMPT_PATH = Path("prompts/agents/job_analysis_prompt.md")
_EXPERIENCE_PROMPT_PATH = Path("prompts/experience_prompt.md")
_SKILLS_PROMPT_PATH = Path("prompts/skills_highlight_prompt.md")
_SKILLS_SELECT_PROMPT_PATH = Path("prompts/skills_select_prompt.md")
_SUMMARY_PROMPT_PATH = Path("prompts/experience_summary_prompt.md")
_TEMPLATES_PATH = Path("prompts/experience_templates.yaml")

_NUM_RE = re.compile(r"\d+(?:\.\d+)?%?")
# Delays (seconds) before 2nd and 3rd attempts when the agent CLI returns an error.
# Covers transient rate-limit / busy-server responses from Claude Code or Gemini CLI.
_AGENT_RETRY_DELAYS: tuple[int, ...] = (5, 15)


class AgentChainProvider:
    """5-agent chained LLM provider using claude -p (Claude Code subscription)."""

    name = "agents"

    def __init__(self, config: AgentChainConfig) -> None:
        self._config = config
        self._warnings: list[str] = []

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]:
        _ = instructions
        if not items:
            return []

        job_analysis = load_job_analysis(self._config.context_dir)

        # Collect allowed numbers from all original bullets
        allowed_numbers: set[str] = set()
        for item in items:
            for bullet in item.bullets:
                allowed_numbers.update(_NUM_RE.findall(bullet))

        prompt = build_bullet_polish_prompt(tuple(items), job_analysis)
        try:
            output = self._run_agent(prompt, timeout=self._config.timeout_bullet_polish)
        except ValueError as exc:
            self._warn(f"Bullet polish agent failed ({exc}); returning input unchanged")
            return [
                BulletRewriteResult(item_id=item.item_id, bullets=item.bullets) for item in items
            ]

        return parse_bullet_polish_response(
            output,
            tuple(items),
            allowed_numbers=allowed_numbers,
            max_bullet_chars=self._config.max_bullet_chars,
            warnings=self._warnings,
        )

    def generate_experience(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> Sequence[ExperienceDraft]:
        # Agent 1: run job analysis if job is provided
        job_analysis = self._ensure_job_analysis(job)

        # Agent 2: experience generation with job context injected
        templates = load_experience_templates(_TEMPLATES_PATH)
        prompt = build_experience_prompt(
            _EXPERIENCE_PROMPT_PATH,
            templates=templates,
            projects=tuple(projects),
            job=job,
        )
        prompt = _inject_job_context(prompt, job_analysis)
        output = self._run_agent(prompt, timeout=self._config.timeout_experience)
        return parse_experience_drafts(output)

    def highlight_skills(
        self,
        skills: Sequence[str],
        profile: Profile,
        job: JobSpec | None,
    ) -> Sequence[str]:
        job_analysis = self._ensure_job_analysis(job)

        prompt = build_skills_prompt(
            _SKILLS_PROMPT_PATH,
            skills=tuple(skills),
            profile=profile,
            job=job,
        )
        prompt = _inject_job_context(prompt, job_analysis)
        output = self._run_agent(prompt, timeout=self._config.timeout_skills)
        payload = _extract_json_payload(output)
        highlighted = list(parse_skill_highlights(payload, allowed_skills=tuple(skills)))

        # Check keyword coverage against required_skills from job analysis
        if job_analysis and job_analysis.required_skills:
            required_lower = {s.lower() for s in job_analysis.required_skills}
            highlighted_lower = {s.lower() for s in highlighted}
            coverage = len(required_lower & highlighted_lower) / len(required_lower)
            if coverage < self._config.keyword_coverage_min:
                self._warn(
                    f"Skill keyword coverage {coverage:.0%} below threshold "
                    f"{self._config.keyword_coverage_min:.0%}"
                )

        return highlighted

    def select_skills(
        self,
        skills_with_scores: Sequence[tuple[str, int, int]],
        profile: Profile,
        job: JobSpec,
    ) -> Sequence[str]:
        job_analysis = self._ensure_job_analysis(job)

        prompt = build_skills_select_prompt(
            _SKILLS_SELECT_PROMPT_PATH,
            skills_with_scores=tuple(skills_with_scores),
            profile=profile,
            job=job,
        )
        prompt = _inject_job_context(prompt, job_analysis)
        output = self._run_agent(prompt, timeout=self._config.timeout_skills)
        payload = _extract_json_payload(output)
        allowed = tuple(s for s, _, __ in skills_with_scores)
        return parse_skill_selection(payload, allowed_skills=allowed)

    def generate_experience_summary(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> str:
        job_analysis = self._ensure_job_analysis(job)

        prompt = build_experience_summary_prompt(
            _SUMMARY_PROMPT_PATH,
            projects=tuple(projects),
            job=job,
        )
        prompt = _inject_job_context(prompt, job_analysis)
        output = self._run_agent(prompt, timeout=self._config.timeout_summary)
        payload = _extract_json_payload(output)
        summary = parse_experience_summary(payload)

        # Enforce max summary chars, truncating at sentence boundary
        if len(summary) > self._config.max_summary_chars:
            truncated = summary[: self._config.max_summary_chars]
            last_period = truncated.rfind(".")
            if last_period > self._config.max_summary_chars // 2:
                truncated = truncated[: last_period + 1]
            self._warn(f"Summary truncated from {len(summary)} to {len(truncated)} chars")
            summary = truncated

        return summary

    def _ensure_job_analysis(self, job: JobSpec | None) -> JobAnalysis | None:
        """Load existing or generate new job analysis. Returns None if no job."""
        if job is None:
            return None
        existing = load_job_analysis(self._config.context_dir)
        if existing is not None:
            return existing
        return self._run_job_analysis_agent(job)

    def _run_job_analysis_agent(self, job: JobSpec) -> JobAnalysis | None:
        """Agent 1: analyze job description and write job_analysis.yaml."""
        prompt_path = _JOB_ANALYSIS_PROMPT_PATH
        if not prompt_path.exists():
            self._warn(f"Job analysis prompt not found at {prompt_path}; skipping Agent 1")
            return None

        prompt = prompt_path.read_text(encoding="utf-8")
        job_payload = {
            "id": job.id,
            "title": job.title,
            "raw_text": job.raw_text,
            "keywords": list(job.keywords),
        }
        prompt = prompt.replace("{{JOB}}", yaml.safe_dump(job_payload, sort_keys=False).strip())

        try:
            output = self._run_agent(prompt, timeout=self._config.timeout_job_analysis)
        except ValueError as exc:
            self._warn(f"Job analysis agent failed ({exc}); continuing without job context")
            return None

        try:
            analysis = parse_job_analysis(output)
        except ValueError as exc:
            self._warn(f"Job analysis parse failed ({exc}); continuing without job context")
            return None

        write_job_analysis(analysis, self._config.context_dir)
        return analysis

    def _run_agent(self, prompt: str, *, timeout: int) -> str:
        """Run the AI CLI subprocess with the given prompt. Returns output text.

        Retries up to len(_AGENT_RETRY_DELAYS) extra times on transient failures
        (non-zero exit codes, empty output, timeouts) — covers rate-limit / busy-server
        responses from Claude Code or Gemini CLI free tier.
        """
        cfg = self._config.codex
        cmd = [cfg.command, *cfg.args]
        last_exc: ValueError | None = None

        for attempt in range(1, len(_AGENT_RETRY_DELAYS) + 2):
            if attempt > 1:
                delay = _AGENT_RETRY_DELAYS[attempt - 2]
                print(
                    f"[agents] attempt {attempt - 1} failed ({last_exc}); "
                    f"retrying in {delay}s — this can happen when the AI service is busy",
                    file=sys.stderr,
                )
                time.sleep(delay)

            try:
                if cfg.prompt_mode == "arg":
                    result = subprocess.run(
                        cmd + [prompt],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
            except FileNotFoundError as exc:
                # Binary not on PATH — not a transient error, fail immediately
                raise ValueError(f"agent chain failed: command not found ({cfg.command})") from exc
            except subprocess.TimeoutExpired:
                last_exc = ValueError(f"agent chain timed out after {timeout}s")
                continue

            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                last_exc = ValueError(f"agent chain failed: {stderr or 'unknown error'}")
                continue

            output = (result.stdout or "").strip()
            if not output:
                last_exc = ValueError("agent chain returned empty output")
                continue

            return output

        raise last_exc  # type: ignore[misc]

    def _warn(self, message: str) -> None:
        self._warnings.append(message)
        print(f"WARNING [agents]: {message}", file=sys.stderr)


def _inject_job_context(prompt: str, job_analysis: JobAnalysis | None) -> str:
    """Substitute {{JOB_CONTEXT}} in prompt with formatted job analysis (or empty string)."""
    context = format_job_analysis_context(job_analysis) if job_analysis else ""
    return prompt.replace("{{JOB_CONTEXT}}", context)
