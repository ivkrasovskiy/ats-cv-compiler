"""
Tests for frontmatter parsing error handling.

Covers the failure mode where a YAML URL field contains markdown link syntax
(e.g. [text](url)) inserted by a rich-text editor, which produces invalid YAML
and should raise a descriptive ValueError rather than a raw yaml.ParserError.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cv_compiler.parse.frontmatter import parse_markdown_frontmatter


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.md"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestFrontmatterErrors:
    def test_markdown_link_in_url_field_raises_value_error(self, tmp_path: Path) -> None:
        """Markdown link syntax [label](url) inside YAML is invalid and must raise ValueError."""
        p = _write(
            tmp_path,
            """\
            ---
            id: profile
            name: Test User
            links:
              - label: LinkedIn
                url: [https://linkedin.com/in/test/](https://linkedin.com/in/test/)
            ---
            """,
        )
        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_markdown_frontmatter(p)

    def test_yaml_error_message_includes_filename(self, tmp_path: Path) -> None:
        """The ValueError message must include the filename so the user knows which file to fix."""
        p = _write(
            tmp_path,
            """\
            ---
            id: profile
            name: [broken
            ---
            """,
        )
        with pytest.raises(ValueError, match=p.name):
            parse_markdown_frontmatter(p)

    def test_yaml_error_includes_bracket_hint(self, tmp_path: Path) -> None:
        """When markdown link syntax is detected, the error should hint about brackets."""
        p = _write(
            tmp_path,
            """\
            ---
            id: profile
            links:
              - label: LinkedIn
                url: [https://linkedin.com](LinkedIn)
            ---
            """,
        )
        with pytest.raises(ValueError, match="bracket"):
            parse_markdown_frontmatter(p)

    def test_valid_url_parses_correctly(self, tmp_path: Path) -> None:
        """A plain URL (no brackets) must parse without error."""
        p = _write(
            tmp_path,
            """\
            ---
            id: profile
            links:
              - label: LinkedIn
                url: https://linkedin.com/in/test/
            ---
            """,
        )
        doc = parse_markdown_frontmatter(p)
        links = doc.frontmatter["links"]
        assert links[0]["url"] == "https://linkedin.com/in/test/"

    def test_missing_closing_delimiter_raises_value_error(self, tmp_path: Path) -> None:
        """A file with an opening --- but no closing --- must raise ValueError."""
        p = _write(
            tmp_path,
            """\
            ---
            id: profile
            name: Test
            """,
        )
        with pytest.raises(ValueError, match="closing frontmatter delimiter"):
            parse_markdown_frontmatter(p)

    def test_empty_file_returns_empty_frontmatter(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.md"
        p.write_text("", encoding="utf-8")
        doc = parse_markdown_frontmatter(p)
        assert doc.frontmatter == {}
        assert doc.body == ""

    def test_file_without_frontmatter_returns_body(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "Just plain text\nno frontmatter\n")
        doc = parse_markdown_frontmatter(p)
        assert doc.frontmatter == {}
        assert "plain text" in doc.body
