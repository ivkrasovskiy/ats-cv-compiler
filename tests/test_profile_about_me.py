"""
Tests for profile about_me parsing.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cv_compiler.parse.loaders import load_canonical_data


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestProfileAboutMe(unittest.TestCase):
    def test_about_me_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "data" / "profile.md",
                """---
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
""",
            )
            _write(
                root / "data" / "skills.md",
                """---
id: skills
categories:
  - name: "Languages"
    items: ["Python"]
---
""",
            )
            data = load_canonical_data(root / "data")
            self.assertEqual(data.profile.about_me, "Builds software.")
