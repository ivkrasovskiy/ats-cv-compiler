"""
Tests for LLM skill highlight parsing.
"""

from __future__ import annotations

import unittest

from cv_compiler.llm.skills import parse_skill_highlights


class TestSkillHighlights(unittest.TestCase):
    def test_parse_skill_highlights_valid(self) -> None:
        allowed = ("Python", "Docker", "Redis")
        text = '{"highlighted_skills": ["docker", "Python"]}'
        result = parse_skill_highlights(text, allowed_skills=allowed)
        self.assertEqual(result, ("Docker", "Python"))

    def test_parse_skill_highlights_rejects_unknown(self) -> None:
        allowed = ("Python", "Docker")
        text = '{"highlighted_skills": ["Kubernetes"]}'
        with self.assertRaises(ValueError):
            parse_skill_highlights(text, allowed_skills=allowed)
