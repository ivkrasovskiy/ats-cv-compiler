"""
Tests for parse_skill_selection and build_skills_select_prompt.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.skills import build_skills_select_prompt, parse_skill_selection
from cv_compiler.schema.models import JobSpec, Link, Profile

_PROMPT_TEMPLATE = (
    "headline: {{PROFILE_HEADLINE}}\njob: {{JOB}}\nskills: {{SKILLS}}\nctx: {{JOB_CONTEXT}}\n"
)


def _profile() -> Profile:
    return Profile(
        id="profile",
        name="Test User",
        headline="Senior ML Engineer",
        location="Remote",
        email=None,
        links=(),
        about_me="Builds models.",
    )


def _job() -> JobSpec:
    return JobSpec(
        id="acme_ml",
        title="ML Engineer",
        raw_text="pytorch transformers python",
        keywords=("pytorch", "python"),
        source_path=None,
    )


class TestParseSkillSelection(unittest.TestCase):
    def test_valid_returns_correct_tuple(self) -> None:
        allowed = ("Python", "Docker", "Redis")
        result = parse_skill_selection(
            json.dumps({"selected_skills": ["Python", "Docker"]}),
            allowed_skills=allowed,
        )
        self.assertEqual(result, ("Python", "Docker"))

    def test_case_insensitive_returns_canonical_casing(self) -> None:
        allowed = ("Python", "Docker")
        result = parse_skill_selection(
            json.dumps({"selected_skills": ["python", "DOCKER"]}),
            allowed_skills=allowed,
        )
        self.assertEqual(result, ("Python", "Docker"))

    def test_unknown_skill_raises_value_error(self) -> None:
        with self.assertRaises(ValueError, msg="Unknown skill should raise"):
            parse_skill_selection(
                json.dumps({"selected_skills": ["Kubernetes"]}),
                allowed_skills=("Python",),
            )

    def test_invalid_json_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_skill_selection("{not valid json", allowed_skills=("Python",))

    def test_duplicates_are_deduplicated(self) -> None:
        allowed = ("Python",)
        result = parse_skill_selection(
            json.dumps({"selected_skills": ["python", "Python"]}),
            allowed_skills=allowed,
        )
        self.assertEqual(result, ("Python",))

    def test_empty_selection(self) -> None:
        result = parse_skill_selection(
            json.dumps({"selected_skills": []}),
            allowed_skills=("Python", "Go"),
        )
        self.assertEqual(result, ())

    def test_missing_key_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_skill_selection(
                json.dumps({"highlighted_skills": ["Python"]}),
                allowed_skills=("Python",),
            )

    def test_non_list_value_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_skill_selection(
                json.dumps({"selected_skills": "Python"}),
                allowed_skills=("Python",),
            )


class TestBuildSkillsSelectPrompt(unittest.TestCase):
    def _write_prompt(self, directory: str) -> Path:
        p = Path(directory) / "skills_select_prompt.md"
        p.write_text(_PROMPT_TEMPLATE, encoding="utf-8")
        return p

    def test_contains_profile_headline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = self._write_prompt(tmp)
            result = build_skills_select_prompt(
                prompt_path,
                skills_with_scores=(("PyTorch", 1, 0),),
                profile=_profile(),
                job=_job(),
            )
        self.assertIn("Senior ML Engineer", result)

    def test_contains_skill_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = self._write_prompt(tmp)
            result = build_skills_select_prompt(
                prompt_path,
                skills_with_scores=(("PyTorch", 1, 0), ("TensorFlow", 0, 0)),
                profile=_profile(),
                job=_job(),
            )
        self.assertIn("PyTorch", result)
        self.assertIn("TensorFlow", result)

    def test_contains_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = self._write_prompt(tmp)
            result = build_skills_select_prompt(
                prompt_path,
                skills_with_scores=(("PyTorch", 1, 0),),
                profile=_profile(),
                job=_job(),
            )
        # Scores are serialised as YAML; exact_matches and fuzzy_matches must appear
        self.assertIn("exact_matches", result)
        self.assertIn("fuzzy_matches", result)

    def test_contains_job_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = self._write_prompt(tmp)
            result = build_skills_select_prompt(
                prompt_path,
                skills_with_scores=(("Python", 1, 0),),
                profile=_profile(),
                job=_job(),
            )
        self.assertIn("acme_ml", result)

    def test_no_unresolved_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = self._write_prompt(tmp)
            result = build_skills_select_prompt(
                prompt_path,
                skills_with_scores=(("Python", 1, 0),),
                profile=_profile(),
                job=_job(),
            )
        self.assertNotIn("{{", result)
