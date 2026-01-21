"""
Tests for experience file selection precedence.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.parse.loaders import load_canonical_data


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _profile_md() -> str:
    return """---
id: profile
name: "Test User"
headline: "Engineer"
location: "Remote"
email: "test@example.com"
links:
  - label: "GitHub"
    url: "https://github.com/test"
about_me: "Builds software."
---
"""


def _skills_md() -> str:
    return """---
id: skills
categories:
  - name: "Languages"
    items: ["Python"]
---
"""


def _project_md() -> str:
    return """---
id: proj_one
name: "Project One"
company: "Example Corp"
role: "Engineer"
start_date: "2023-01"
end_date: null
tags: ["python"]
bullets:
  - "Improved throughput by 20%."
---
"""


def _experience_md(bullet: str) -> str:
    return f"""---
id: exp_one
company: "Example Corp"
title: "Engineer"
location: "Remote"
start_date: "2023-01"
end_date: null
tags: ["python"]
bullets:
  - "{bullet}"
---
"""


class TestExperienceLoading(unittest.TestCase):
    def test_user_prefix_overrides_llm_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "data" / "profile.md", _profile_md())
            _write(root / "data" / "skills.md", _skills_md())
            _write(root / "data" / "projects" / "one.md", _project_md())
            _write(root / "data" / "experience" / "llm_exp_one.md", _experience_md("LLM bullet"))
            _write(root / "data" / "experience" / "exp_one.md", _experience_md("Manual bullet"))
            _write(
                root / "data" / "experience" / "user_exp_one.1700000000.md",
                _experience_md("Archived user bullet"),
            )
            _write(root / "data" / "experience" / "user_exp_one.md", _experience_md("User bullet"))

            data = load_canonical_data(root / "data")
            self.assertEqual(len(data.experience), 1)
            self.assertEqual(data.experience[0].bullets[0], "User bullet")

    def test_llm_prefix_used_when_no_user_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "data" / "profile.md", _profile_md())
            _write(root / "data" / "skills.md", _skills_md())
            _write(root / "data" / "projects" / "one.md", _project_md())
            _write(root / "data" / "experience" / "llm_exp_one.md", _experience_md("LLM bullet"))
            _write(root / "data" / "experience" / "exp_one.md", _experience_md("Manual bullet"))

            data = load_canonical_data(root / "data")
            self.assertEqual(len(data.experience), 1)
            self.assertEqual(data.experience[0].bullets[0], "LLM bullet")
