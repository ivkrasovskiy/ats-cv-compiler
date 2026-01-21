"""
Tests for PDF ingestion helpers.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.ingest.pdf_ingest import (
    ParsedCv,
    ParsedExperience,
    ParsedProfile,
    ParsedSkillCategory,
    parse_ingest_payload,
    write_ingest_files,
)
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter


class TestPdfIngest(unittest.TestCase):
    def test_parse_ingest_payload(self) -> None:
        payload = {
            "profile": {
                "name": "Jane Doe",
                "headline": "Engineer",
                "location": "Remote",
                "email": "jane@example.com",
                "links": [{"label": "GitHub", "url": "https://github.com/jane"}],
                "about_me": "Builds reliable systems.",
            },
            "experience": [
                {
                    "company": "Acme",
                    "title": "Developer",
                    "location": "Remote",
                    "start_date": "2022-01",
                    "end_date": "",
                    "bullets": ["Did a thing."],
                    "tags": ["python"],
                }
            ],
            "projects": [],
            "skills": [{"name": "Languages", "items": ["Python"]}],
            "education": [],
        }
        parsed = parse_ingest_payload(payload)
        self.assertEqual(parsed.profile.name, "Jane Doe")
        self.assertEqual(parsed.experience[0].company, "Acme")
        self.assertEqual(parsed.skills[0].name, "Languages")

    def test_write_ingest_files(self) -> None:
        profile = ParsedProfile(
            name="Jane Doe",
            headline="Engineer",
            location="Remote",
            email="jane@example.com",
            about_me="Builds reliable systems.",
            links=(),
        )
        experience = (
            ParsedExperience(
                company="Acme",
                title="Developer",
                location=None,
                start_date="2022-01",
                end_date=None,
                bullets=("Did a thing.",),
                tags=("python",),
            ),
        )
        skills = (ParsedSkillCategory(name="Languages", items=("Python",)),)
        parsed = ParsedCv(
            profile=profile,
            experience=experience,
            projects=(),
            skills=skills,
            education=(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            result = write_ingest_files(data_dir, parsed, overwrite=False)
            self.assertTrue(result.written_paths)
            profile_doc = parse_markdown_frontmatter(data_dir / "profile.md")
            self.assertEqual(profile_doc.frontmatter["name"], "Jane Doe")
            exp_files = list((data_dir / "experience").glob("user_*.md"))
            self.assertEqual(len(exp_files), 1)
