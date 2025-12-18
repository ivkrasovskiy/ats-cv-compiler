"""
CLI argument parsing and command dispatch.

This module owns the user-facing `cv` command, including flags like `--example` and `--job`.
The heavy lifting is delegated to the pipeline layer.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from cv_compiler.pipeline import BuildRequest, build_cv
from cv_compiler.render.types import RenderFormat


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cv", description="Compile structured career data into ATS-safe CVs."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Generate a CV (generic or job-targeted).")
    build_inputs = build.add_mutually_exclusive_group()
    build_inputs.add_argument(
        "--data", type=str, default=None, help="Path to canonical data directory (default: ./data)."
    )
    build_inputs.add_argument(
        "--example",
        type=str,
        default=None,
        help="Use a bundled example dataset by name (e.g. basic).",
    )
    build.add_argument(
        "--job", type=str, default=None, help="Path to a job description (e.g. jobs/acme.md)."
    )
    build.add_argument(
        "--llm",
        type=str,
        default=None,
        help="Optional LLM provider name. Deterministic build does not require this.",
    )

    sub.add_parser("lint", help="Validate schema and enforce ATS constraints.")

    explain = sub.add_parser("explain", help="Explain deterministic selection decisions.")
    explain.add_argument(
        "--job", type=str, required=True, help="Path to a job description (e.g. jobs/acme.md)."
    )

    return parser


def _resolve_example_root(name: str) -> Path:
    return Path("examples") / name


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    match args.command:
        case "build":
            example_root = _resolve_example_root(args.example) if args.example else None
            data_dir = (
                Path(args.data)
                if args.data
                else (example_root / "data" if example_root else Path("data"))
            )
            template_dir = example_root / "templates" if example_root else Path("templates")
            out_dir = example_root / "out" if example_root else Path("out")
            job_path = Path(args.job) if args.job else None

            try:
                build_cv(
                    BuildRequest(
                        data_dir=data_dir,
                        job_path=job_path,
                        template_dir=template_dir,
                        out_dir=out_dir,
                        format=RenderFormat.PDF,
                        llm=None,
                        llm_instructions_path=None,
                    )
                )
            except NotImplementedError:
                print("`cv build` is scaffolded but not implemented yet.", file=sys.stderr)
                return 1
            return 0
        case "lint":
            print("`cv lint` is scaffolded but not implemented yet.", file=sys.stderr)
            return 1
        case "explain":
            print("`cv explain` is scaffolded but not implemented yet.", file=sys.stderr)
            return 1
        case _:
            parser.error(f"Unknown command: {args.command}")
            return 2
