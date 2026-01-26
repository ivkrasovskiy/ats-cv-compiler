#!/usr/bin/env python3
"""
Generate the one-time experience summary file via Codex.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cv_compiler.llm.codex import CodexExecConfig, CodexExecProvider
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.pipeline import _format_experience_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate data/experience_summary.md using Codex.",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data",
        help="Path to canonical data directory (default: ./data).",
    )
    parser.add_argument(
        "--job",
        type=str,
        default=None,
        help="Optional job description to bias the summary.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing experience_summary.md file.",
    )
    args = parser.parse_args()

    data_dir = Path(args.data)
    summary_path = data_dir / "experience_summary.md"
    if summary_path.exists() and not args.overwrite:
        print(f"Summary already exists: {summary_path}", file=sys.stderr)
        return 0

    try:
        data = load_canonical_data(data_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load data: {exc}", file=sys.stderr)
        return 2

    job = load_job_spec(Path(args.job)) if args.job else None
    provider = CodexExecProvider(CodexExecConfig.from_env(env_path=Path("config/llm.env")))
    try:
        summary = provider.generate_experience_summary(tuple(data.projects), job)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to generate summary: {exc}", file=sys.stderr)
        return 1

    summary_path.write_text(_format_experience_summary(summary), encoding="utf-8")
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
