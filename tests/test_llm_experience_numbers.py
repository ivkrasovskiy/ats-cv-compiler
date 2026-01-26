"""
Tests for allowed numeric tokens in LLM experience bullets.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.base import ExperienceDraft
from cv_compiler.llm.experience import write_experience_artifacts
from cv_compiler.schema.models import ProjectEntry


class TestLlmExperienceNumbers(unittest.TestCase):
    def test_dates_allowed_in_bullets(self) -> None:
        project = ProjectEntry(
            id="proj_acme",
            name="Importer",
            company="Acme",
            role="Engineer",
            start_date="2024-01",
            end_date="2024-12",
            tags=(),
            bullets=("Built import pipeline.",),
        )
        draft = ExperienceDraft(
            id="exp_acme_2024",
            role=None,
            source_project_ids=("proj_acme",),
            bullets=("Improved data quality in 2024.",),
            keywords=(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            written = write_experience_artifacts(
                data_dir,
                projects=(project,),
                drafts=(draft,),
            )

            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].exists())
