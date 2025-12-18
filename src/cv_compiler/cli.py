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

from cv_compiler.explain import format_selection_explanation
from cv_compiler.lint.linter import lint_build_inputs
from cv_compiler.llm.base import NoopProvider
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.pipeline import BuildRequest, build_cv
from cv_compiler.render.types import RenderFormat
from cv_compiler.select.selector import select_content
from cv_compiler.types import Severity


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

    lint = sub.add_parser("lint", help="Validate schema and enforce ATS constraints.")
    lint_inputs = lint.add_mutually_exclusive_group()
    lint_inputs.add_argument(
        "--data", type=str, default=None, help="Path to canonical data directory."
    )
    lint_inputs.add_argument(
        "--example", type=str, default=None, help="Use a bundled example dataset by name."
    )

    explain = sub.add_parser("explain", help="Explain deterministic selection decisions.")
    explain.add_argument(
        "--job", type=str, required=True, help="Path to a job description (e.g. jobs/acme.md)."
    )
    explain_inputs = explain.add_mutually_exclusive_group()
    explain_inputs.add_argument(
        "--data", type=str, default=None, help="Path to canonical data directory."
    )
    explain_inputs.add_argument(
        "--example", type=str, default=None, help="Use a bundled example dataset by name."
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

            llm = None
            if args.llm:
                if args.llm == "noop":
                    llm = NoopProvider()
                else:
                    print(
                        f"Unknown/unsupported LLM provider: {args.llm!r} (supported: noop)",
                        file=sys.stderr,
                    )
                    return 2

            try:
                result = build_cv(
                    BuildRequest(
                        data_dir=data_dir,
                        job_path=job_path,
                        template_dir=template_dir,
                        out_dir=out_dir,
                        format=RenderFormat.PDF,
                        llm=llm,
                        llm_instructions_path=None,
                    )
                )
            except NotImplementedError as e:
                print(f"Build failed: {e}", file=sys.stderr)
                return 1

            errors = [i for i in result.issues if i.severity == Severity.ERROR]
            for issue in result.issues:
                where = f" ({issue.source_path})" if issue.source_path else ""
                print(
                    f"{issue.severity.value.upper()} {issue.code}: {issue.message}{where}",
                    file=sys.stderr,
                )
            if errors:
                return 1

            print(result.output_path)
            return 0
        case "lint":
            example_root = _resolve_example_root(args.example) if args.example else None
            data_dir = (
                Path(args.data)
                if args.data
                else (example_root / "data" if example_root else Path("data"))
            )

            try:
                data = load_canonical_data(data_dir)
            except Exception as e:  # noqa: BLE001
                print(f"Failed to load data: {e}", file=sys.stderr)
                return 1

            issues = lint_build_inputs(data)
            errors = [i for i in issues if i.severity == Severity.ERROR]
            for issue in issues:
                where = f" ({issue.source_path})" if issue.source_path else ""
                print(
                    f"{issue.severity.value.upper()} {issue.code}: {issue.message}{where}",
                    file=sys.stderr,
                )
            return 1 if errors else 0
        case "explain":
            example_root = _resolve_example_root(args.example) if args.example else None
            data_dir = (
                Path(args.data)
                if args.data
                else (example_root / "data" if example_root else Path("data"))
            )
            job_path = Path(args.job)

            try:
                data = load_canonical_data(data_dir)
                job = load_job_spec(job_path)
            except Exception as e:  # noqa: BLE001
                print(f"Failed to load inputs: {e}", file=sys.stderr)
                return 1

            selection = select_content(data, job)
            print(format_selection_explanation(selection))
            return 0
        case _:
            parser.error(f"Unknown command: {args.command}")
            return 2
