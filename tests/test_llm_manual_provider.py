"""
Tests for the manual/offline LLM provider.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cv_compiler.llm.manual import ManualProvider
from cv_compiler.schema.models import ProjectEntry


class TestManualProvider(unittest.TestCase):
    def test_manual_provider_writes_request_and_reads_response(self) -> None:
        root = Path(__file__).resolve().parents[1]
        prompt_path = root / "prompts" / "experience_prompt.md"
        templates_path = root / "prompts" / "experience_templates.yaml"

        project = ProjectEntry(
            id="proj_test",
            name="Test Project",
            company="Example Corp",
            role="Engineer",
            start_date="2023-01",
            end_date=None,
            tags=(),
            bullets=("Reduced manual edits by 10%.",),
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            request_path = tmp_dir / "llm_request.json"
            response_path = tmp_dir / "llm_response.json"
            response_path.write_text("experiences: []\n", encoding="utf-8")

            provider = ManualProvider(
                request_path=request_path,
                response_path=response_path,
                model="manual",
                prompt_path=prompt_path,
                templates_path=templates_path,
            )
            drafts = provider.generate_experience((project,), None)
            self.assertEqual(drafts, ())
            self.assertTrue(request_path.exists())
            payload = json.loads(request_path.read_text(encoding="utf-8"))["payload"]
            self.assertIn("messages", payload)

    def test_manual_provider_requires_response_file(self) -> None:
        root = Path(__file__).resolve().parents[1]
        prompt_path = root / "prompts" / "experience_prompt.md"
        templates_path = root / "prompts" / "experience_templates.yaml"

        project = ProjectEntry(
            id="proj_test",
            name="Test Project",
            company="Example Corp",
            role="Engineer",
            start_date="2023-01",
            end_date=None,
            tags=(),
            bullets=("Reduced manual edits by 10%.",),
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            provider = ManualProvider(
                request_path=tmp_dir / "llm_request.json",
                response_path=tmp_dir / "llm_response.json",
                model="manual",
                prompt_path=prompt_path,
                templates_path=templates_path,
            )
            with self.assertRaises(ValueError):
                provider.generate_experience((project,), None)
