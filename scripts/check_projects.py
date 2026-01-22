#!/usr/bin/env python3
"""
Validate project Markdown files and report per-file issues.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cv_compiler.tools.project_check import collect_project_issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate project Markdown files in a canonical data directory."
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data",
        help="Path to canonical data directory (default: ./data).",
    )
    args = parser.parse_args()
    data_dir = Path(args.data)
    projects_dir = data_dir / "projects"

    issues = collect_project_issues(projects_dir)
    errors = 0
    for issue in issues:
        where = f" ({issue.path})"
        print(f"{issue.severity} {issue.code}: {issue.message}{where}", file=sys.stderr)
        if issue.severity == "ERROR":
            errors += 1

    if errors:
        return 1
    if not issues:
        print("OK: no project issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
