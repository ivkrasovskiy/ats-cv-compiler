"""
Tests for Markdown normalization to ASCII.
"""

from __future__ import annotations

import unittest

from cv_compiler.render.markdown import build_markdown
from cv_compiler.schema.models import (
    CanonicalData,
    Education,
    ExperienceEntry,
    Link,
    Profile,
    Skills,
    SkillsCategory,
)
from cv_compiler.select.types import SelectionDecision, SelectionResult


class TestMarkdownNormalization(unittest.TestCase):
    def test_build_markdown_strips_unicode(self) -> None:
        profile = Profile(
            id="profile",
            name="Jose O\u2019Neil",
            headline="Engineer",
            location="Remote",
            email=None,
            links=(Link(label="Site", url="https://example.com"),),
            about_me="Builds systems\u2014reliably.",
        )
        experience = ExperienceEntry(
            id="exp_1",
            company="Acme",
            title="Dev",
            location=None,
            start_date="2022-01",
            end_date=None,
            tags=(),
            bullets=("Improved uptime\u2013stability.",),
        )
        skills = Skills(id="skills", categories=(SkillsCategory(name="Tools", items=("Git",)),))
        data = CanonicalData(
            profile=profile,
            experience=(experience,),
            projects=(),
            skills=skills,
            education=Education(id="education", entries=(), languages=()),
        )
        selection = SelectionResult(
            selected_experience_ids=("exp_1",),
            selected_project_ids=(),
            decisions=(
                SelectionDecision(item_id="exp_1", score=1.0, matched_keywords=(), reasons=()),
            ),
        )

        markdown = build_markdown(data, selection)
        self.assertIn("Jose O'Neil", markdown)
        self.assertIn("Builds systems-reliably.", markdown)
        self.assertIn("**Improved** uptime-stability.", markdown)
        self.assertTrue(all(ord(ch) < 128 for ch in markdown))

    def test_experience_bullet_emphasis(self) -> None:
        profile = Profile(
            id="profile",
            name="Test User",
            headline="Engineer",
            location="Remote",
            email=None,
            links=(),
            about_me="Builds systems.",
        )
        experience = ExperienceEntry(
            id="exp_1",
            company="Acme",
            title="Dev",
            location=None,
            start_date="2022-01",
            end_date=None,
            tags=(),
            bullets=("Increased coverage by 3-5% through new tests.",),
        )
        skills = Skills(id="skills", categories=(SkillsCategory(name="Tools", items=("Git",)),))
        data = CanonicalData(
            profile=profile,
            experience=(experience,),
            projects=(),
            skills=skills,
            education=Education(id="education", entries=(), languages=()),
        )
        selection = SelectionResult(
            selected_experience_ids=("exp_1",),
            selected_project_ids=(),
            decisions=(
                SelectionDecision(item_id="exp_1", score=1.0, matched_keywords=(), reasons=()),
            ),
        )

        markdown = build_markdown(data, selection)
        self.assertIn("Increased coverage by **3-5%** through new tests.", markdown)
