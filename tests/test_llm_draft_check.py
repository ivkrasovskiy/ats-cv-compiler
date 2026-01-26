"""
Tests for LLM draft validation helpers.
"""

from __future__ import annotations

import unittest

from cv_compiler.schema.models import ProjectEntry
from cv_compiler.tools.llm_draft_check import collect_draft_issues


class TestLlmDraftCheck(unittest.TestCase):
    def test_unknown_project_id(self) -> None:
        projects = (
            ProjectEntry(
                id="proj_one",
                name="Project One",
                company="Acme",
                role="Engineer",
                start_date="2023-01",
                end_date=None,
                tags=(),
                bullets=("Did work.",),
            ),
        )
        draft_text = """
experiences:
  - id: exp_acme_2023
    role: Engineer
    source_project_ids: [proj_missing]
    keywords: [\"analytics\"]
    bullets:
      - "Improved throughput by 10%."
"""
        issues = collect_draft_issues(draft_text=draft_text, projects=projects)
        codes = [issue.code for issue in issues]
        self.assertIn("UNKNOWN_PROJECT_ID", codes)

    def test_missing_role_warning(self) -> None:
        projects = (
            ProjectEntry(
                id="proj_one",
                name="Project One",
                company="Acme",
                role=None,
                start_date="2023-01",
                end_date=None,
                tags=(),
                bullets=("Did work.",),
            ),
        )
        draft_text = """
experiences:
  - id: exp_acme_2023
    role: null
    source_project_ids: [proj_one]
    keywords: []
    bullets:
      - "Improved throughput by 10%."
"""
        issues = collect_draft_issues(draft_text=draft_text, projects=projects)
        codes = [issue.code for issue in issues]
        self.assertIn("MISSING_ROLE", codes)
