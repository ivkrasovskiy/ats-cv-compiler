"""
Contract tests for LLM provider implementations.

Tests run against real implementations with controlled inputs.
No network calls — all tested via pure functions or temp files.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from cv_compiler.llm.base import BulletRewriteRequest, NoopProvider
from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.llm.provider import resolve_from_env
from cv_compiler.llm.skills import parse_skill_highlights

# ── §1-3 NoopProvider ─────────────────────────────────────────────────────────


def test_noop_rewrite_returns_bullets_unchanged():
    provider = NoopProvider()
    req = BulletRewriteRequest(
        item_id="x",
        bullets=("Built X.", "Improved Y."),
        job_keywords=("python",),
    )
    results = provider.rewrite_bullets([req], instructions=None)
    assert len(results) == 1
    assert results[0].item_id == "x"
    assert results[0].bullets == ("Built X.", "Improved Y.")


def test_noop_generate_experience_returns_empty():
    provider = NoopProvider()
    result = provider.generate_experience(projects=[], job=None)
    assert list(result) == []


def test_noop_highlight_skills_returns_empty():
    provider = NoopProvider()
    result = provider.highlight_skills(skills=["Python", "Go"], profile=None, job=None)  # type: ignore[arg-type]
    assert list(result) == []


# ── §4 parse_skill_highlights — unknown skill rejected ────────────────────────


def test_parse_skill_highlights_rejects_unknown_skill():
    allowed = ("Python", "Go", "Kubernetes")
    response = json.dumps({"highlighted_skills": ["Ruby"]})  # not in allowed
    with pytest.raises(ValueError) as exc_info:
        parse_skill_highlights(response, allowed_skills=allowed)
    assert "ruby" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()


# ── §5 parse_skill_highlights — capped at 5 ──────────────────────────────────


def test_parse_skill_highlights_caps_at_five():
    skills = tuple(f"Skill{i}" for i in range(10))
    response = json.dumps({"highlighted_skills": list(skills)})
    result = parse_skill_highlights(response, allowed_skills=skills)
    assert len(result) <= 5


# ── §6 CodexExecConfig — default command ─────────────────────────────────────


def test_codex_config_default_command(monkeypatch, tmp_path):
    env_file = tmp_path / "llm.env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.delenv("CV_CODEX_CMD", raising=False)
    monkeypatch.delenv("CV_CODEX_ARGS", raising=False)
    monkeypatch.delenv("CV_CODEX_MODEL", raising=False)
    monkeypatch.delenv("CV_CODEX_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("CV_CODEX_PROMPT_MODE", raising=False)
    monkeypatch.delenv("CV_CODEX_PROGRESS", raising=False)
    config = CodexExecConfig.from_env(env_path=env_file)
    assert config.command == "codex"


# ── §7 CodexExecConfig — env var overrides file ───────────────────────────────


def test_codex_config_env_var_overrides_file(monkeypatch, tmp_path):
    env_file = tmp_path / "llm.env"
    env_file.write_text("CV_CODEX_CMD=from_file\n", encoding="utf-8")
    monkeypatch.setenv("CV_CODEX_CMD", "from_env")
    config = CodexExecConfig.from_env(env_path=env_file)
    assert config.command == "from_env"


# ── §8 CodexExecConfig — invalid timeout falls back to default ────────────────


def test_codex_config_invalid_timeout_uses_default(monkeypatch, tmp_path):
    env_file = tmp_path / "llm.env"
    env_file.write_text("CV_CODEX_TIMEOUT_SECONDS=notanumber\n", encoding="utf-8")
    monkeypatch.delenv("CV_CODEX_TIMEOUT_SECONDS", raising=False)
    config = CodexExecConfig.from_env(env_path=env_file)
    assert config.timeout_seconds in {300, 600}


# ── §9 CodexExecConfig — invalid prompt mode falls back to stdin ──────────────


def test_codex_config_invalid_prompt_mode_defaults_to_stdin(monkeypatch, tmp_path):
    env_file = tmp_path / "llm.env"
    env_file.write_text("CV_CODEX_PROMPT_MODE=badvalue\n", encoding="utf-8")
    monkeypatch.delenv("CV_CODEX_PROMPT_MODE", raising=False)
    config = CodexExecConfig.from_env(env_path=env_file)
    assert config.prompt_mode == "stdin"


# ── helpers for provider resolution tests ─────────────────────────────────────


def _resolve(provider: str, extra: str = "") -> object:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(f"CV_AI_PROVIDER={provider}\n{extra}")
        tmp = f.name
    try:
        # Ensure env var doesn't interfere with file-based provider
        saved = os.environ.pop("CV_AI_PROVIDER", None)
        try:
            return resolve_from_env(Path(tmp))
        finally:
            if saved is not None:
                os.environ["CV_AI_PROVIDER"] = saved
    finally:
        os.unlink(tmp)


# ── §10 Gemini default model ──────────────────────────────────────────────────


def test_provider_gemini_default_model_is_flash():
    r = _resolve("gemini")
    assert r.ingest_mode == "cli"  # type: ignore[union-attr]
    assert r.codex_config is not None  # type: ignore[union-attr]
    assert r.codex_config.model == "gemini-2.0-flash"  # type: ignore[union-attr]


# ── §11 Custom without base URL → llm_config is None ─────────────────────────


def test_provider_custom_without_base_url_returns_none_llm_config():
    r = _resolve("custom")  # no CV_LLM_BASE_URL
    assert r.llm_config is None  # type: ignore[union-attr]


# ── §12 Unknown provider falls back to API mode ───────────────────────────────


def test_provider_unknown_falls_back_to_api_mode():
    r = _resolve("someunknownvalue")
    assert r.ingest_mode == "api"  # type: ignore[union-attr]
