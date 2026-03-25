"""
Tests for PDF ingestion helpers.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cv_compiler.ingest.pdf_ingest import (
    ParsedCv,
    ParsedExperience,
    ParsedProfile,
    ParsedSkillCategory,
    _cli_llm_content,
    parse_ingest_payload,
    write_ingest_files,
)
from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter


class TestPdfIngest(unittest.TestCase):
    def test_parse_ingest_payload(self) -> None:
        payload = {
            "profile": {
                "name": "Jane Doe",
                "headline": "Engineer",
                "location": "Remote",
                "email": "jane@example.com",
                "links": [{"label": "GitHub", "url": "https://github.com/jane"}],
                "about_me": "Builds reliable systems.",
            },
            "experience": [
                {
                    "company": "Acme",
                    "title": "Developer",
                    "location": "Remote",
                    "start_date": "2022-01",
                    "end_date": "",
                    "bullets": ["Did a thing."],
                    "tags": ["python"],
                }
            ],
            "projects": [],
            "skills": [{"name": "Languages", "items": ["Python"]}],
            "education": [],
        }
        parsed = parse_ingest_payload(payload)
        self.assertEqual(parsed.profile.name, "Jane Doe")
        self.assertEqual(parsed.experience[0].company, "Acme")
        self.assertEqual(parsed.skills[0].name, "Languages")

    def test_write_ingest_files(self) -> None:
        profile = ParsedProfile(
            name="Jane Doe",
            headline="Engineer",
            location="Remote",
            email="jane@example.com",
            about_me="Builds reliable systems.",
            links=(),
        )
        experience = (
            ParsedExperience(
                company="Acme",
                title="Developer",
                location=None,
                start_date="2022-01",
                end_date=None,
                bullets=("Did a thing.",),
                tags=("python",),
            ),
        )
        skills = (ParsedSkillCategory(name="Languages", items=("Python",)),)
        parsed = ParsedCv(
            profile=profile,
            experience=experience,
            projects=(),
            skills=skills,
            education=(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            result = write_ingest_files(data_dir, parsed, overwrite=False)
            self.assertTrue(result.written_paths)
            profile_doc = parse_markdown_frontmatter(data_dir / "profile.md")
            self.assertEqual(profile_doc.frontmatter["name"], "Jane Doe")
            proj_files = list((data_dir / "projects").glob("*.md"))
            self.assertEqual(len(proj_files), 1)

    def test_write_ingest_files_overwrite_removes_old(self) -> None:
        profile = ParsedProfile(
            name="Jane Doe",
            headline="Engineer",
            location="Remote",
            email="jane@example.com",
            about_me="Builds reliable systems.",
            links=(),
        )
        experience = (
            ParsedExperience(
                company="Acme",
                title="Developer",
                location=None,
                start_date="2022-01",
                end_date=None,
                bullets=("Did a thing.",),
                tags=("python",),
            ),
        )
        skills = (ParsedSkillCategory(name="Languages", items=("Python",)),)
        parsed = ParsedCv(
            profile=profile,
            experience=experience,
            projects=(),
            skills=skills,
            education=(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            projects_dir = data_dir / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            old_path = projects_dir / "old.md"
            old_path.write_text("old", encoding="utf-8")

            write_ingest_files(data_dir, parsed, overwrite=True)

            self.assertFalse(old_path.exists())
            proj_files = list(projects_dir.glob("*.md"))
            self.assertEqual(len(proj_files), 1)
            backup_root = data_dir.parent / "tmp"
            if backup_root.exists():
                backups = list(backup_root.glob("ingest_backup_*"))
                self.assertEqual(backups, [])


class TestCliLlmContent(unittest.TestCase):
    _VALID_RESPONSE = json.dumps({"answer": "42"})

    def _config(self, *, prompt_mode: str, model: str | None = None) -> CodexExecConfig:
        return CodexExecConfig(
            command="mycli",
            args=("-p",),
            model=model,
            timeout_seconds=30,
            prompt_mode=prompt_mode,
            progress=False,
        )

    def _make_completed(self, stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess([], returncode, stdout.encode(), b"")

    def test_stdin_mode_pipes_prompt(self) -> None:
        """Claude path: prompt sent via stdin, cmd has no trailing prompt arg."""
        with patch("subprocess.run", return_value=self._make_completed(self._VALID_RESPONSE)) as mock_run:
            result = _cli_llm_content(self._config(prompt_mode="stdin"), "hello")
        self.assertEqual(result, self._VALID_RESPONSE)
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        self.assertEqual(cmd, ["mycli", "-p"])
        self.assertEqual(call_args[1]["input"], b"hello")

    def test_arg_mode_appends_prompt(self) -> None:
        """Gemini path: prompt appended as arg to -p, no stdin."""
        with patch("subprocess.run", return_value=self._make_completed(self._VALID_RESPONSE)) as mock_run:
            result = _cli_llm_content(self._config(prompt_mode="arg"), "hello")
        self.assertEqual(result, self._VALID_RESPONSE)
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        self.assertEqual(cmd, ["mycli", "-p", "hello"])
        self.assertIsNone(call_args[1]["input"])

    def test_nonzero_exit_raises(self) -> None:
        with patch("subprocess.run", return_value=self._make_completed("", returncode=1)):
            with self.assertRaises(ValueError, msg="CLI LLM failed"):
                _cli_llm_content(self._config(prompt_mode="arg"), "hi")

    def test_command_not_found_raises(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(ValueError, msg="CLI command not found"):
                _cli_llm_content(self._config(prompt_mode="stdin"), "hi")

    def test_model_sets_gemini_model_env(self) -> None:
        """When model is set, GEMINI_MODEL env var is passed to subprocess."""
        config = self._config(prompt_mode="arg", model="gemini-2.0-flash")
        with patch("subprocess.run", return_value=self._make_completed(self._VALID_RESPONSE)) as mock_run:
            _cli_llm_content(config, "hello")
        env = mock_run.call_args[1].get("env")
        self.assertIsNotNone(env)
        self.assertEqual(env["GEMINI_MODEL"], "gemini-2.0-flash")

    def test_no_model_passes_no_env(self) -> None:
        """When model is None, env is not overridden."""
        config = self._config(prompt_mode="arg", model=None)
        with patch("subprocess.run", return_value=self._make_completed(self._VALID_RESPONSE)) as mock_run:
            _cli_llm_content(config, "hello")
        env = mock_run.call_args[1].get("env")
        self.assertIsNone(env)


class TestProviderResolution(unittest.TestCase):
    def _resolve(self, provider: str, gemini_model: str | None = None) -> object:
        from cv_compiler.llm.provider import resolve_from_env
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"CV_AI_PROVIDER={provider}\n")
            if gemini_model:
                f.write(f"CV_GEMINI_MODEL={gemini_model}\n")
            tmp = f.name
        try:
            return resolve_from_env(Path(tmp))
        finally:
            os.unlink(tmp)

    def test_gemini_uses_flash_default(self) -> None:
        r = self._resolve("gemini")
        self.assertEqual(r.ingest_mode, "cli")
        self.assertIsNotNone(r.codex_config)
        self.assertEqual(r.codex_config.command, "gemini")
        self.assertEqual(r.codex_config.model, "gemini-2.0-flash")

    def test_gemini_custom_model(self) -> None:
        r = self._resolve("gemini", gemini_model="gemini-2.5-pro")
        self.assertEqual(r.codex_config.model, "gemini-2.5-pro")

    def test_claude_ingest_mode(self) -> None:
        r = self._resolve("claude")
        self.assertEqual(r.ingest_mode, "cli")
        self.assertEqual(r.codex_config.command, "claude")
        self.assertIsNone(r.codex_config.model)
        self.assertEqual(r.codex_config.prompt_mode, "stdin")

    def test_custom_uses_api_mode(self) -> None:
        import tempfile, os as _os
        from cv_compiler.llm.provider import resolve_from_env
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("CV_AI_PROVIDER=custom\nCV_LLM_BASE_URL=http://localhost:1234\nCV_LLM_MODEL=test\n")
            tmp = f.name
        try:
            r = resolve_from_env(Path(tmp))
        finally:
            _os.unlink(tmp)
        self.assertEqual(r.ingest_mode, "api")
        self.assertIsNone(r.codex_config)
        self.assertIsNotNone(r.llm_config)
