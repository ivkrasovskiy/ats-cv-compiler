"""
Tests for parsing LLM experience responses with extra text.
"""

from __future__ import annotations

import unittest

from cv_compiler.llm.experience import parse_experience_drafts


class TestLLMExperienceParsing(unittest.TestCase):
    def test_parse_experience_drafts_strips_think(self) -> None:
        text = """
<think>
Reasoning that should be ignored.
</think>

experiences:
  - id: exp_example_corp_2023-02
    role: Software Engineer
    source_project_ids: [proj_cv_compiler]
    bullets:
      - "Improved throughput by 20%."
"""
        drafts = parse_experience_drafts(text)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].source_project_ids, ("proj_cv_compiler",))
