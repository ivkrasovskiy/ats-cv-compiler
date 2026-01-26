"""
Codex CLI-backed LLM provider.

Runs `codex exec` to produce structured experience drafts and skill highlights.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from cv_compiler.llm.base import (
    BulletRewriteRequest,
    BulletRewriteResult,
    ExperienceDraft,
    LLMProvider,
)
from cv_compiler.llm.config import read_env_file
from cv_compiler.llm.experience import (
    build_experience_prompt,
    load_experience_templates,
    parse_experience_drafts,
)
from cv_compiler.llm.skills import build_skills_prompt, parse_skill_highlights
from cv_compiler.schema.models import JobSpec, Profile, ProjectEntry


@dataclass(frozen=True, slots=True)
class CodexExecConfig:
    command: str
    args: tuple[str, ...]
    model: str | None
    timeout_seconds: int
    prompt_mode: str
    progress: bool

    @staticmethod
    def from_env(
        *,
        env_path: Path | None = Path("config/llm.env"),
    ) -> CodexExecConfig:
        file_values = read_env_file(env_path) if env_path else {}
        command = os.getenv("CV_CODEX_CMD") or file_values.get("CV_CODEX_CMD") or "codex"
        args_raw = os.getenv("CV_CODEX_ARGS") or file_values.get("CV_CODEX_ARGS") or ""
        args = tuple(shlex.split(args_raw))
        model = (
            os.getenv("CV_CODEX_MODEL")
            or file_values.get("CV_CODEX_MODEL")
            or "gpt-5.2"
        )
        timeout_raw = os.getenv("CV_CODEX_TIMEOUT_SECONDS") or file_values.get(
            "CV_CODEX_TIMEOUT_SECONDS"
        )
        prompt_mode = (
            os.getenv("CV_CODEX_PROMPT_MODE") or file_values.get("CV_CODEX_PROMPT_MODE") or "stdin"
        )
        if prompt_mode not in {"stdin", "arg"}:
            prompt_mode = "stdin"
        progress_raw = os.getenv("CV_CODEX_PROGRESS") or file_values.get("CV_CODEX_PROGRESS")
        progress = _parse_bool(progress_raw)
        timeout = _parse_timeout(timeout_raw) if timeout_raw else 600
        return CodexExecConfig(
            command=command,
            args=args,
            model=model,
            timeout_seconds=timeout,
            prompt_mode=prompt_mode,
            progress=progress,
        )


class CodexExecProvider(LLMProvider):
    name = "codex"

    def __init__(
        self,
        config: CodexExecConfig,
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
        output = self._run_codex(prompt)
        return parse_experience_drafts(output)

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
        output = self._run_codex(prompt)
        payload = _extract_json_payload(output)
        return parse_skill_highlights(payload, allowed_skills=tuple(skills))

    def _run_codex(self, prompt: str) -> str:
        exec_args = _ensure_full_auto(self._config.args)
        exec_args, use_json, last_message_path, cleanup = _prepare_json_exec(
            exec_args,
            enable_progress=self._config.progress,
        )
        cmd = [self._config.command, "exec", *exec_args]
        if self._config.model:
            cmd.extend(["--model", self._config.model])
        try:
            if use_json and self._config.progress:
                result = _run_codex_with_spinner(
                    cmd,
                    prompt=prompt,
                    prompt_mode=self._config.prompt_mode,
                    timeout=self._config.timeout_seconds,
                )
            elif self._config.prompt_mode == "arg":
                result = subprocess.run(
                    cmd + [prompt],
                    capture_output=True,
                    text=True,
                    timeout=self._config.timeout_seconds,
                    check=False,
                )
            else:
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self._config.timeout_seconds,
                    check=False,
                )
        except FileNotFoundError as exc:
            raise ValueError(
                f"codex exec failed: command not found ({self._config.command})"
            ) from exc
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise ValueError(f"codex exec failed: {stderr or 'unknown error'}")
        output = (result.stdout or "").strip()
        if use_json:
            output = _read_last_message(last_message_path)
            if cleanup:
                try:
                    last_message_path.unlink()
                except OSError:
                    pass
        if not output:
            raise ValueError("codex exec returned empty output")
        return output


def _parse_timeout(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        return 300
    return value if value > 0 else 300


def _parse_bool(raw: str | None) -> bool:
    if not raw:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _extract_json_payload(raw: str) -> str:
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            json.loads(snippet)
            return snippet
        except json.JSONDecodeError:
            pass
    raise ValueError("LLM skill highlight response must be valid JSON")


def _ensure_full_auto(args: tuple[str, ...]) -> tuple[str, ...]:
    if _has_exec_mode_flag(args):
        return args
    return args + ("--full-auto",)


def _has_exec_mode_flag(args: tuple[str, ...]) -> bool:
    flags = {"--full-auto", "--dangerously-bypass-approvals-and-sandbox"}
    return any(arg in flags for arg in args)


def _prepare_json_exec(
    args: tuple[str, ...],
    *,
    enable_progress: bool,
) -> tuple[tuple[str, ...], bool, Path, bool]:
    args_list = list(args)
    has_json = "--json" in args_list
    use_json = enable_progress or has_json
    if enable_progress and not has_json:
        args_list.append("--json")
    last_message_path = Path()
    cleanup = False
    if use_json:
        last_message_path = _get_output_last_message(args_list)
        if last_message_path == Path():
            handle = tempfile.NamedTemporaryFile(delete=False, prefix="codex_last_", suffix=".txt")
            last_message_path = Path(handle.name)
            handle.close()
            args_list.extend(["--output-last-message", str(last_message_path)])
            cleanup = True
    return tuple(args_list), use_json, last_message_path, cleanup


def _get_output_last_message(args: list[str]) -> Path:
    for idx, value in enumerate(args):
        if value == "--output-last-message" and idx + 1 < len(args):
            return Path(args[idx + 1])
    return Path()


def _run_codex_with_spinner(
    cmd: list[str],
    *,
    prompt: str,
    prompt_mode: str,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    if prompt_mode == "arg":
        proc = subprocess.Popen(
            cmd + [prompt],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdin is not None
        proc.stdin.write(prompt)
        proc.stdin.close()
    start = time.monotonic()
    spinner = "|/-\\"
    idx = 0
    while True:
        ret = proc.poll()
        if ret is not None:
            break
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            proc.kill()
            raise ValueError("codex exec timed out")
        msg = f"\rcodex: {spinner[idx % len(spinner)]} {elapsed:.0f}s"
        print(msg, end="", file=sys.stderr, flush=True)
        idx += 1
        time.sleep(0.5)
    print("\rcodex: done".ljust(24), file=sys.stderr)
    stderr = ""
    if proc.stderr is not None:
        stderr = proc.stderr.read()
    return subprocess.CompletedProcess(
        cmd,
        proc.returncode,
        stdout="",
        stderr=stderr,
    )


def _read_last_message(path: Path) -> str:
    if not path.exists():
        raise ValueError("codex exec did not produce a final message")
    return path.read_text(encoding="utf-8").strip()
