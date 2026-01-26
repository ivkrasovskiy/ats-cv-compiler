"""
Tests for Codex exec config parsing.
"""

from __future__ import annotations

import os
import unittest
from contextlib import contextmanager

from cv_compiler.llm.codex import CodexExecConfig, _ensure_full_auto


@contextmanager
def _temp_env(values: dict[str, str]) -> object:
    keys = list(values.keys())
    old = {key: os.environ.get(key) for key in keys}
    try:
        for key, value in values.items():
            os.environ[key] = value
        yield
    finally:
        for key in keys:
            if old[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old[key]


@contextmanager
def _clear_env(keys: list[str]) -> object:
    old = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TestCodexExecConfig(unittest.TestCase):
    def test_defaults(self) -> None:
        keys = [
            "CV_CODEX_CMD",
            "CV_CODEX_ARGS",
            "CV_CODEX_MODEL",
            "CV_CODEX_TIMEOUT_SECONDS",
            "CV_CODEX_PROMPT_MODE",
        ]
        with _clear_env(keys):
            config = CodexExecConfig.from_env(env_path=None)
        self.assertEqual(config.command, "codex")
        self.assertEqual(config.args, ())
        self.assertEqual(config.model, "gpt-5.2")
        self.assertEqual(config.timeout_seconds, 600)
        self.assertEqual(config.prompt_mode, "stdin")

    def test_args_and_prompt_mode(self) -> None:
        with _temp_env(
            {
                "CV_CODEX_ARGS": '-c mcp_config="config/mcp.json" --full-auto',
                "CV_CODEX_PROMPT_MODE": "arg",
            }
        ):
            config = CodexExecConfig.from_env(env_path=None)
        self.assertEqual(
            config.args,
            ("-c", "mcp_config=config/mcp.json", "--full-auto"),
        )
        self.assertEqual(config.prompt_mode, "arg")

    def test_invalid_prompt_mode_falls_back(self) -> None:
        with _temp_env({"CV_CODEX_PROMPT_MODE": "unknown"}):
            config = CodexExecConfig.from_env(env_path=None)
        self.assertEqual(config.prompt_mode, "stdin")

    def test_full_auto_default(self) -> None:
        self.assertEqual(_ensure_full_auto(()), ("--full-auto",))

    def test_full_auto_respects_existing(self) -> None:
        self.assertEqual(_ensure_full_auto(("--full-auto",)), ("--full-auto",))
        self.assertEqual(
            _ensure_full_auto(("--dangerously-bypass-approvals-and-sandbox",)),
            ("--dangerously-bypass-approvals-and-sandbox",),
        )
