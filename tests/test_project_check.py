"""
Tests for project file validation helper.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.tools.project_check import collect_project_issues


class TestProjectCheck(unittest.TestCase):
    def test_reports_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            projects_dir = Path(tmp) / "data" / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            bad_path = projects_dir / "proj_bad.md"
            bad_path.write_text("---\nname: Test\n---\n", encoding="utf-8")

            issues = collect_project_issues(projects_dir)
            messages = [issue.message for issue in issues if issue.path == bad_path]

            self.assertTrue(any("`id`" in msg for msg in messages))
            self.assertTrue(any("`tags`" in msg for msg in messages))
            self.assertTrue(any("`bullets`" in msg for msg in messages))

    def test_reports_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            projects_dir = Path(tmp) / "data" / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            content = "---\nid: proj_dup\nname: Test\nbullets: [\"One\"]\ntags: [\"tag\"]\n---\n"
            (projects_dir / "proj_one.md").write_text(content, encoding="utf-8")
            (projects_dir / "proj_two.md").write_text(content, encoding="utf-8")

            issues = collect_project_issues(projects_dir)
            codes = [issue.code for issue in issues]

            self.assertIn("PROJECT_ID_DUPLICATE", codes)
