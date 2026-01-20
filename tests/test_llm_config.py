"""
Tests for loading LLM config from env files.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.config import LLMConfig


class TestLLMConfig(unittest.TestCase):
    def test_from_env_reads_file_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "llm.env"
            env_path.write_text(
                "CV_LLM_BASE_URL=http://127.0.0.1:1234\nCV_LLM_MODEL=qwen\nCV_LLM_TIMEOUT_SECONDS=42\n",
                encoding="utf-8",
            )
            config = LLMConfig.from_env(env_path=env_path)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.base_url, "http://127.0.0.1:1234")
            self.assertEqual(config.model, "qwen")
            self.assertEqual(config.timeout_seconds, 42)

    def test_env_overrides_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "llm.env"
            env_path.write_text(
                "CV_LLM_BASE_URL=http://file\nCV_LLM_MODEL=file-model\nCV_LLM_TIMEOUT_SECONDS=10\n",
                encoding="utf-8",
            )
            old_base = os.environ.get("CV_LLM_BASE_URL")
            old_model = os.environ.get("CV_LLM_MODEL")
            old_timeout = os.environ.get("CV_LLM_TIMEOUT_SECONDS")
            os.environ["CV_LLM_BASE_URL"] = "http://env"
            os.environ["CV_LLM_MODEL"] = "env-model"
            os.environ["CV_LLM_TIMEOUT_SECONDS"] = "99"
            try:
                config = LLMConfig.from_env(env_path=env_path)
                self.assertIsNotNone(config)
                assert config is not None
                self.assertEqual(config.base_url, "http://env")
                self.assertEqual(config.model, "env-model")
                self.assertEqual(config.timeout_seconds, 99)
            finally:
                if old_base is None:
                    os.environ.pop("CV_LLM_BASE_URL", None)
                else:
                    os.environ["CV_LLM_BASE_URL"] = old_base
                if old_model is None:
                    os.environ.pop("CV_LLM_MODEL", None)
                else:
                    os.environ["CV_LLM_MODEL"] = old_model
                if old_timeout is None:
                    os.environ.pop("CV_LLM_TIMEOUT_SECONDS", None)
                else:
                    os.environ["CV_LLM_TIMEOUT_SECONDS"] = old_timeout
