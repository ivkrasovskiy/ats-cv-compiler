from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    frontmatter: Mapping[str, Any]
    body: str
    source_path: Path


def parse_markdown_frontmatter(path: Path) -> MarkdownDocument:
    """
    Parse a Markdown document containing YAML frontmatter.

    Expected file shape:
    - Optional YAML frontmatter delimited by `---` lines
    - Markdown body following frontmatter
    """
    raise NotImplementedError
