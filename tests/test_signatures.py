"""
Signature-level tests for the scaffolded public API.

These tests ensure the codebase keeps stable entrypoints/types while implementations are filled in.
"""

from __future__ import annotations

import dataclasses
import inspect
import unittest

from cv_compiler.explain import format_selection_explanation
from cv_compiler.lint.linter import lint_build_inputs, lint_rendered_output
from cv_compiler.llm.base import ExperienceDraft, LLMProvider
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.pipeline import BuildRequest, BuildResult, build_cv
from cv_compiler.render.renderer import render_cv
from cv_compiler.render.types import RenderRequest, RenderResult
from cv_compiler.schema.models import CanonicalData, JobSpec, Profile
from cv_compiler.select.selector import select_content
from cv_compiler.select.types import SelectionDecision, SelectionResult
from cv_compiler.types import LintIssue, Severity


class TestSignatures(unittest.TestCase):
    def test_enums_exist(self) -> None:
        self.assertTrue(issubclass(Severity, str))
        self.assertIn("ERROR", Severity.__members__)
        self.assertIn("WARNING", Severity.__members__)

    def test_core_dataclasses_exist(self) -> None:
        for cls in [
            LintIssue,
            Profile,
            CanonicalData,
            JobSpec,
            ExperienceDraft,
            SelectionDecision,
            SelectionResult,
            RenderRequest,
            RenderResult,
            BuildRequest,
            BuildResult,
        ]:
            self.assertTrue(dataclasses.is_dataclass(cls), cls.__name__)

    def test_pipeline_signature(self) -> None:
        sig = inspect.signature(build_cv)
        self.assertEqual(list(sig.parameters), ["request"])

    def test_parse_signatures(self) -> None:
        self.assertEqual(list(inspect.signature(parse_markdown_frontmatter).parameters), ["path"])
        self.assertEqual(list(inspect.signature(load_canonical_data).parameters), ["data_dir"])
        self.assertEqual(list(inspect.signature(load_job_spec).parameters), ["path"])

    def test_selection_signature(self) -> None:
        sig = inspect.signature(select_content)
        self.assertEqual(list(sig.parameters), ["data", "job"])

    def test_render_signature(self) -> None:
        self.assertEqual(list(inspect.signature(render_cv).parameters), ["request"])

    def test_lint_signatures(self) -> None:
        self.assertEqual(list(inspect.signature(lint_build_inputs).parameters), ["data"])
        self.assertEqual(list(inspect.signature(lint_rendered_output).parameters), ["output_path"])

    def test_explain_signature(self) -> None:
        self.assertEqual(
            list(inspect.signature(format_selection_explanation).parameters), ["selection"]
        )

    def test_llm_provider_protocol_shape(self) -> None:
        self.assertTrue(hasattr(LLMProvider, "rewrite_bullets"))
        self.assertTrue(hasattr(LLMProvider, "generate_experience"))
