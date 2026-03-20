"""
Tests for URL label rendering in build_markdown contact line.

Verifies that links with a label emit [label](url) markdown format,
and links with an empty label emit the bare URL.
"""

from __future__ import annotations

import unittest

from cv_compiler.render.markdown import build_markdown
from cv_compiler.schema.models import (
    CanonicalData,
    Education,
    Link,
    Profile,
    Skills,
    SkillsCategory,
)
from cv_compiler.select.types import SelectionResult


def _data(links: tuple[Link, ...]) -> CanonicalData:
    return CanonicalData(
        profile=Profile(
            id="profile",
            name="Test User",
            headline="Engineer",
            location="Remote",
            email=None,
            links=links,
            about_me="Builds things.",
        ),
        experience=(),
        projects=(),
        skills=Skills(
            id="skills",
            categories=(SkillsCategory(name="Tools", items=("Git",)),),
        ),
        education=Education(id="education", entries=(), languages=()),
    )


_EMPTY_SELECTION = SelectionResult(
    selected_experience_ids=(),
    selected_project_ids=(),
    decisions=(),
)


class TestUrlLabels(unittest.TestCase):
    def test_link_with_label_renders_markdown_link(self) -> None:
        md = build_markdown(
            _data((Link(label="LinkedIn", url="https://linkedin.com/in/x"),)),
            _EMPTY_SELECTION,
        )
        self.assertIn("[LinkedIn](https://linkedin.com/in/x)", md)

    def test_link_with_empty_label_renders_bare_url(self) -> None:
        md = build_markdown(
            _data((Link(label="", url="https://github.com/x"),)),
            _EMPTY_SELECTION,
        )
        self.assertIn("https://github.com/x", md)
        # No empty markdown link format
        self.assertNotIn("[](", md)

    def test_labeled_and_unlabeled_links_coexist(self) -> None:
        md = build_markdown(
            _data((
                Link(label="LinkedIn", url="https://linkedin.com/in/x"),
                Link(label="", url="https://github.com/x"),
            )),
            _EMPTY_SELECTION,
        )
        self.assertIn("[LinkedIn](https://linkedin.com/in/x)", md)
        self.assertIn("https://github.com/x", md)

    def test_multiple_labeled_links(self) -> None:
        md = build_markdown(
            _data((
                Link(label="LinkedIn", url="https://linkedin.com/in/x"),
                Link(label="Telegram", url="https://t.me/x"),
            )),
            _EMPTY_SELECTION,
        )
        self.assertIn("[LinkedIn](https://linkedin.com/in/x)", md)
        self.assertIn("[Telegram](https://t.me/x)", md)

    def test_link_without_url_is_skipped(self) -> None:
        """A Link with an empty URL is not included in the contact line at all."""
        md = build_markdown(
            _data((Link(label="NoURL", url=""),)),
            _EMPTY_SELECTION,
        )
        self.assertNotIn("NoURL", md)
        self.assertNotIn("[NoURL]", md)
