"""
Smoke tests for building the bundled example dataset.

These tests verify that the deterministic pipeline can produce an ATS-safe PDF without requiring
an LLM or network access at runtime.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from cv_compiler.pipeline import BuildRequest, build_cv
from cv_compiler.render.types import RenderFormat
from cv_compiler.types import Severity


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestBuildExample(unittest.TestCase):
    def test_build_example_generic_is_deterministic(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data_dir = root / "examples" / "basic" / "data"
        template_dir = root / "examples" / "basic" / "templates"

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result1 = build_cv(
                BuildRequest(
                    data_dir=data_dir,
                    job_path=None,
                    template_dir=template_dir,
                    out_dir=out_dir,
                    format=RenderFormat.PDF,
                    llm=None,
                    llm_instructions_path=None,
                )
            )
            self.assertTrue(result1.output_path.exists())
            self.assertEqual(result1.output_path.name, "cv_generic.pdf")
            self.assertTrue(result1.output_path.read_bytes().startswith(b"%PDF"))
            self.assertFalse(any(i.severity == Severity.ERROR for i in result1.issues))
            digest1 = _sha256(result1.output_path)

            result2 = build_cv(
                BuildRequest(
                    data_dir=data_dir,
                    job_path=None,
                    template_dir=template_dir,
                    out_dir=out_dir,
                    format=RenderFormat.PDF,
                    llm=None,
                    llm_instructions_path=None,
                )
            )
            digest2 = _sha256(result2.output_path)
            self.assertEqual(digest1, digest2)

    def test_build_example_job_specific(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data_dir = root / "examples" / "basic" / "data"
        template_dir = root / "examples" / "basic" / "templates"
        job_path = root / "examples" / "basic" / "jobs" / "backend_engineer.md"

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = build_cv(
                BuildRequest(
                    data_dir=data_dir,
                    job_path=job_path,
                    template_dir=template_dir,
                    out_dir=out_dir,
                    format=RenderFormat.PDF,
                    llm=None,
                    llm_instructions_path=None,
                )
            )
            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.output_path.name.startswith("cv_job_backend_engineer."))
            self.assertTrue(result.output_path.read_bytes().startswith(b"%PDF"))
