"""
Tests for LLM experience backup helpers.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.experience import (
    backup_llm_experience_files,
    restore_llm_experience_files,
)


class TestLlmExperienceBackup(unittest.TestCase):
    def test_backup_and_restore_llm_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            experience_dir = data_dir / "experience"
            experience_dir.mkdir(parents=True, exist_ok=True)
            llm_path = experience_dir / "llm_exp_one.md"
            user_path = experience_dir / "user_exp_one.md"
            llm_path.write_text("llm", encoding="utf-8")
            user_path.write_text("user", encoding="utf-8")

            backup_dir = backup_llm_experience_files(data_dir)

            self.assertIsNotNone(backup_dir)
            self.assertFalse(llm_path.exists())
            self.assertTrue(user_path.exists())
            self.assertTrue((backup_dir / "llm_exp_one.md").exists())

            restore_llm_experience_files(backup_dir, data_dir)

            self.assertTrue(llm_path.exists())
            self.assertTrue(user_path.exists())
            self.assertFalse(backup_dir.exists())

    def test_backup_skips_when_no_llm_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            experience_dir = data_dir / "experience"
            experience_dir.mkdir(parents=True, exist_ok=True)
            user_path = experience_dir / "user_exp_one.md"
            user_path.write_text("user", encoding="utf-8")

            backup_dir = backup_llm_experience_files(data_dir)

            self.assertIsNone(backup_dir)
            self.assertTrue(user_path.exists())
