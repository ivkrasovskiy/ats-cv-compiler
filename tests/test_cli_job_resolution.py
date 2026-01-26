"""
Tests for job path resolution logic.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.cli import _resolve_job_paths


class TestJobResolution(unittest.TestCase):
    def test_job_false_forces_generic(self) -> None:
        self.assertEqual(_resolve_job_paths("false"), (None,))

    def test_explicit_job_path(self) -> None:
        self.assertEqual(_resolve_job_paths("jobs/acme.md"), (Path("jobs/acme.md"),))

    def test_defaults_to_jobs_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "jobs"
            jobs_dir.mkdir(parents=True, exist_ok=True)
            (jobs_dir / "b.md").write_text("b", encoding="utf-8")
            (jobs_dir / "a.md").write_text("a", encoding="utf-8")
            (jobs_dir / "README.md").write_text("readme", encoding="utf-8")

            resolved = _resolve_job_paths(None, jobs_dir=jobs_dir)

            self.assertEqual(
                resolved,
                (jobs_dir / "a.md", jobs_dir / "b.md"),
            )

    def test_no_jobs_falls_back_to_generic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jobs_dir = Path(tmp) / "jobs"
            jobs_dir.mkdir(parents=True, exist_ok=True)

            resolved = _resolve_job_paths(None, jobs_dir=jobs_dir)

            self.assertEqual(resolved, (None,))
