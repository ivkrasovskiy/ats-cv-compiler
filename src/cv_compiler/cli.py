"""
CLI argument parsing and command dispatch.

This module owns the user-facing `cv` command, including flags like `--example` and `--job`.
The heavy lifting is delegated to the pipeline layer.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from cv_compiler.explain import format_selection_explanation
from cv_compiler.lint.linter import lint_build_inputs
from cv_compiler.llm import LLMConfig, ManualProvider, NoopProvider, OpenAIProvider
from cv_compiler.llm.config import read_env_file, upsert_env_value
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
        help=(
            "Optional LLM provider name (e.g. openai, noop). "
            "Deterministic build does not require this."
        ),
    )
    build.add_argument(
        "--experience-regenerate",
        action="store_true",
        help="Archive user experience overrides before regenerating with LLM.",
    )
    build.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF rendering; write only the Markdown output.",
    )
    build.add_argument(
        "--from-markdown",
        type=str,
        default=None,
        help="Render PDF from an existing Markdown file instead of parsing data.",
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


def _normalize_llm_mode(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"api", "offline"}:
        return normalized
    return None


def _prompt_llm_mode(env_path: Path) -> str:
    print(
        "Select LLM mode: [1] api (endpoint)  [2] offline (manual copy/paste)",
        file=sys.stderr,
    )
    choice = input("Enter 1 or 2 [1]: ").strip().lower()
    mode = "offline" if choice in {"2", "offline", "o"} else "api"
    try:
        upsert_env_value(env_path, "CV_LLM_MODE", mode)
        print(
            f"Saved CV_LLM_MODE={mode} to {env_path} (edit this file to change).",
            file=sys.stderr,
        )
    except OSError:
        print(
            f"Could not write {env_path}. Set CV_LLM_MODE={mode} in your environment.",
            file=sys.stderr,
        )
    return mode


def _resolve_llm_mode(env_path: Path) -> str:
    env_value = os.getenv("CV_LLM_MODE")
    file_value = read_env_file(env_path).get("CV_LLM_MODE")
    mode = _normalize_llm_mode(env_value) or _normalize_llm_mode(file_value)
    if mode:
        return mode
    if sys.stdin.isatty():
        return _prompt_llm_mode(env_path)
    print(
        "CV_LLM_MODE not set; defaulting to offline. Set CV_LLM_MODE=api to enable endpoint mode.",
        file=sys.stderr,
    )
    return "offline"


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
            render_format = RenderFormat.MARKDOWN if args.no_pdf else RenderFormat.PDF

            if args.from_markdown:
                if args.no_pdf:
                    print("--from-markdown requires PDF output (omit --no-pdf).", file=sys.stderr)
                    return 2
                if args.llm or args.job or args.experience_regenerate:
                    print(
                        "--from-markdown cannot be combined with --llm, --job, or "
                        "--experience-regenerate.",
                        file=sys.stderr,
                    )
                    return 2
                result = build_cv(
                    BuildRequest(
                        data_dir=data_dir,
                        job_path=None,
                        template_dir=template_dir,
                        out_dir=out_dir,
                        format=RenderFormat.PDF,
                        llm=None,
                        llm_instructions_path=None,
                        render_from_markdown=Path(args.from_markdown),
                    )
                )
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

            llm = None
            if args.llm:
                if args.llm == "noop":
                    llm = NoopProvider()
                elif args.llm == "openai":
                    env_path = Path("config/llm.env")
                    mode = _resolve_llm_mode(env_path)
                    if mode == "api":
                        config = LLMConfig.from_env(env_path=env_path)
                        if config is None:
                            print(
                                "Missing LLM config. Set CV_LLM_BASE_URL and CV_LLM_MODEL "
                                "(optional CV_LLM_API_KEY).",
                                file=sys.stderr,
                            )
                            return 2
                        llm = OpenAIProvider(config)
                    else:
                        file_values = read_env_file(env_path)
                        model = (
                            os.getenv("CV_LLM_MODEL") or file_values.get("CV_LLM_MODEL") or "manual"
                        )
                        base_url = os.getenv("CV_LLM_BASE_URL") or file_values.get(
                            "CV_LLM_BASE_URL"
                        )
                        llm = ManualProvider(
                            request_path=out_dir / "llm_request.json",
                            response_path=out_dir / "llm_response.json",
                            model=model,
                            base_url=base_url,
                        )
                else:
                    print(
                        f"Unknown/unsupported LLM provider: {args.llm!r} (supported: openai, noop)",
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
                        format=render_format,
                        llm=llm,
                        llm_instructions_path=None,
                        experience_regenerate=args.experience_regenerate,
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
