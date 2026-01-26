#!/usr/bin/env python3
"""
Validate LLM experience drafts against project data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cv_compiler.parse.loaders import load_canonical_data
from cv_compiler.tools.llm_draft_check import collect_draft_issues, load_draft_text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate LLM experience drafts against canonical project data."
    )
    parser.add_argument(
        "--draft",
        type=str,
        required=True,
        help="Path to an LLM response file (YAML or JSON).",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data",
        help="Path to canonical data directory (default: ./data).",
    )
    args = parser.parse_args()
    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"Draft file not found: {draft_path}", file=sys.stderr)
        return 2

    try:
        data = load_canonical_data(Path(args.data))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load data: {exc}", file=sys.stderr)
        return 2

    draft_text = load_draft_text(draft_path)
    issues = collect_draft_issues(draft_text=draft_text, projects=tuple(data.projects))
    errors = 0
    for issue in issues:
        where = f" [{issue.experience_id}]" if issue.experience_id else ""
        print(
            f"{issue.severity} {issue.code}: {issue.message}{where}",
            file=sys.stderr,
        )
        if issue.severity == "ERROR":
            errors += 1

    if not issues:
        print("OK: no draft issues found.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
