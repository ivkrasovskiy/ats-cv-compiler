"""
Tests for _fuzzy_skill_score and the improved _deterministic_skill_filter.

Covers the fuzzy synonym matching added to the deterministic pipeline path:
- PyTorch / torch, Spark / pyspark, Vertica-SQL / sql
- Skills with zero overlap are still excluded
- Per-category cap of 5 is preserved
"""

from __future__ import annotations

import unittest

from cv_compiler.pipeline import _deterministic_skill_filter, _fuzzy_skill_score
from cv_compiler.schema.models import JobSpec


def _job(raw_text: str, *, keywords: tuple[str, ...] = ()) -> JobSpec:
    return JobSpec(
        id="test",
        title=None,
        raw_text=raw_text,
        keywords=keywords,
        source_path=None,
    )


class TestFuzzySkillScore(unittest.TestCase):
    def test_exact_match_pytorch(self) -> None:
        # "pytorch" == "pytorch" → exact=1, fuzzy=0
        self.assertEqual(_fuzzy_skill_score("PyTorch", {"pytorch"}), (1, 0))

    def test_exact_match_python(self) -> None:
        self.assertEqual(_fuzzy_skill_score("Python", {"python"}), (1, 0))

    def test_fuzzy_torch_in_pytorch(self) -> None:
        # kw "torch" is substring of skill token "pytorch"
        self.assertEqual(_fuzzy_skill_score("PyTorch", {"torch"}), (0, 1))

    def test_fuzzy_spark_in_pyspark(self) -> None:
        # skill token "spark"; kw "pyspark" contains "spark"
        self.assertEqual(_fuzzy_skill_score("Spark", {"pyspark"}), (0, 1))

    def test_fuzzy_sql_in_vertica_sql(self) -> None:
        # "vertica-sql" is one token (hyphen kept); "sql" is substring of it
        self.assertEqual(_fuzzy_skill_score("Vertica-SQL", {"sql"}), (0, 1))

    def test_no_match(self) -> None:
        self.assertEqual(_fuzzy_skill_score("TensorFlow", {"numpy"}), (0, 0))

    def test_both_exact_and_fuzzy_independently(self) -> None:
        # "c#" is one token; job has "c#" (exact) and also "javascript" (no overlap)
        exact, fuzzy = _fuzzy_skill_score("C#", {"c#", "javascript"})
        self.assertEqual(exact, 1)
        self.assertEqual(fuzzy, 0)

    def test_empty_keyword_set(self) -> None:
        self.assertEqual(_fuzzy_skill_score("Python", set()), (0, 0))


class TestDeterministicSkillFilterFuzzy(unittest.TestCase):
    def test_pytorch_included_via_torch_keyword(self) -> None:
        """PyTorch has no exact match on 'torch' but fuzzy score > 0 → included."""
        job = _job("torch")
        result = _deterministic_skill_filter((("ML", ("PyTorch", "NumPy")),), job)
        self.assertIn("PyTorch", result)
        self.assertNotIn("NumPy", result)

    def test_spark_included_via_pyspark_keyword(self) -> None:
        job = _job("pyspark")
        result = _deterministic_skill_filter((("Data", ("Spark", "Hadoop")),), job)
        self.assertIn("Spark", result)
        self.assertNotIn("Hadoop", result)

    def test_zero_score_skills_excluded(self) -> None:
        """Skills with no exact or fuzzy overlap are excluded."""
        job = _job("torch pyspark")
        result = _deterministic_skill_filter(
            (("ML", ("PyTorch", "TensorFlow", "Python")),), job
        )
        self.assertIn("PyTorch", result)
        self.assertNotIn("TensorFlow", result)
        self.assertNotIn("Python", result)

    def test_per_category_cap_at_five(self) -> None:
        job = _job("python go rust java scala kotlin erlang")
        categories = (("Lang", ("Python", "Go", "Rust", "Java", "Scala", "Kotlin", "Erlang")),)
        result = _deterministic_skill_filter(categories, job)
        self.assertLessEqual(len(result), 5)

    def test_preferred_skills_bypass_score_requirement(self) -> None:
        """preferred skills are included even without a keyword match."""
        job = _job("python")
        categories = (("Lang", ("Python", "Go")),)
        result = _deterministic_skill_filter(categories, job, preferred=("Go",))
        self.assertIn("Go", result)
