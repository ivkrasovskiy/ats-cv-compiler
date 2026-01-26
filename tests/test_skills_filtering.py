"""
Tests for skills filtering in Markdown rendering.
"""

from __future__ import annotations

import unittest

from cv_compiler.pipeline import _deterministic_skill_filter
from cv_compiler.render.markdown import build_markdown
from cv_compiler.schema.models import (
    CanonicalData,
    Education,
    ExperienceEntry,
    JobSpec,
    Link,
    Profile,
    ProjectEntry,
    Skills,
    SkillsCategory,
)
from cv_compiler.select.types import SelectionDecision, SelectionResult


class TestSkillsFiltering(unittest.TestCase):
    def test_filters_skills_when_filter_set(self) -> None:
        profile = Profile(
            id="profile",
            name="Test User",
            headline="Engineer",
            location="Remote",
            email=None,
            links=(Link(label="Site", url="https://example.com"),),
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
            keywords=(),
            bullets=("Did work.",),
        )
        skills = Skills(
            id="skills",
            categories=(
                SkillsCategory(name="Languages", items=("Python", "Go")),
                SkillsCategory(name="Data", items=("Postgres", "Kafka")),
            ),
        )
        data = CanonicalData(
            profile=profile,
            experience=(experience,),
            projects=(
                ProjectEntry(
                    id="proj_1",
                    name="Example",
                    company="Acme",
                    role="Dev",
                    start_date="2022-01",
                    end_date=None,
                    tags=(),
                    bullets=("Did work.",),
                ),
            ),
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

        markdown = build_markdown(
            data,
            selection,
            highlighted_skills=("Python",),
            skills_filter=("Python", "Kafka"),
        )

        self.assertIn("**Languages**: **Python**", markdown)
        self.assertIn("**Data**: Kafka", markdown)
        self.assertNotIn("Go", markdown)
        self.assertNotIn("Postgres", markdown)

    def test_deterministic_highlights_per_category(self) -> None:
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
            keywords=(),
            bullets=("Did work.",),
        )
        skills = Skills(
            id="skills",
            categories=(
                SkillsCategory(
                    name="Languages",
                    items=("Python", "Go", "Rust", "Java", "C#", "Scala"),
                ),
                SkillsCategory(
                    name="Data",
                    items=("Postgres", "Kafka", "Spark", "Flink", "Redis", "Snowflake"),
                ),
            ),
        )
        data = CanonicalData(
            profile=profile,
            experience=(experience,),
            projects=(),
            skills=skills,
            education=Education(id="education", entries=(), languages=()),
        )
        job = JobSpec(
            id="job_test",
            title="Backend Engineer",
            raw_text="Python Go Rust Postgres Kafka Spark Flink Redis Snowflake",
            keywords=(),
            source_path=None,
        )
        categories = tuple((cat.name, cat.items) for cat in data.skills.categories)
        selected = _deterministic_skill_filter(categories, job)
        self.assertLessEqual(len([s for s in selected if s in skills.categories[0].items]), 5)
        self.assertLessEqual(len([s for s in selected if s in skills.categories[1].items]), 5)
