"""
Frontmatter parsing for Markdown sources.

Parses Markdown files that include optional YAML frontmatter. Loaders use this to build validated
models from user-editable content.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines:
        return MarkdownDocument(frontmatter={}, body="", source_path=path)

    if lines[0].strip() != "---":
        return MarkdownDocument(frontmatter={}, body=text, source_path=path)

    end_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError(f"Missing closing frontmatter delimiter in {path}")

    yaml_text = "".join(lines[1:end_idx]).strip()
    body = "".join(lines[end_idx + 1 :])
    if not yaml_text:
        frontmatter: Mapping[str, Any] = {}
    else:
        loaded = yaml.safe_load(yaml_text)
        if loaded is None:
            frontmatter = {}
        elif not isinstance(loaded, dict):
            raise ValueError(f"Frontmatter must be a mapping in {path}")
        else:
            frontmatter = loaded

    return MarkdownDocument(frontmatter=frontmatter, body=body, source_path=path)
