"""
Tests for experience role fallback behavior.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.base import ExperienceDraft
from cv_compiler.llm.experience import write_experience_artifacts
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter
from cv_compiler.schema.models import ProjectEntry


class TestLlmExperienceRole(unittest.TestCase):
    def test_allows_role_without_project_role(self) -> None:
        project = ProjectEntry(
            id="proj_acme",
            name="Importer",
            company="Acme",
            role=None,
            start_date="2024-01",
            end_date=None,
            tags=(),
            bullets=("Built import pipeline.",),
        )
        draft = ExperienceDraft(
            id="exp_acme_2024",
            role="Data Engineer",
            source_project_ids=("proj_acme",),
            bullets=("Improved data quality.",),
            keywords=(),
        )
        warnings: list[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            written = write_experience_artifacts(
                data_dir,
                projects=(project,),
                drafts=(draft,),
                warnings=warnings,
            )

            self.assertEqual(len(written), 1)
            doc = parse_markdown_frontmatter(written[0])
            self.assertEqual(doc.frontmatter["title"], "Data Engineer")
            self.assertTrue(any("not found in project data" in w for w in warnings))

    def test_missing_role_skips_entry(self) -> None:
        project = ProjectEntry(
            id="proj_acme",
            name="Importer",
            company="Acme",
            role=None,
            start_date="2024-01",
            end_date=None,
            tags=(),
            bullets=("Built import pipeline.",),
        )
        draft = ExperienceDraft(
            id="exp_acme_2024",
            role=None,
            source_project_ids=("proj_acme",),
            bullets=("Improved data quality.",),
            keywords=(),
        )
        warnings: list[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            written = write_experience_artifacts(
                data_dir,
                projects=(project,),
                drafts=(draft,),
                warnings=warnings,
            )

            self.assertEqual(len(written), 0)
            self.assertTrue(any("Missing role" in w for w in warnings))
