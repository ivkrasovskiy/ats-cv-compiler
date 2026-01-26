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
from cv_compiler.ingest import ingest_pdf_to_markdown
from cv_compiler.lint.linter import lint_build_inputs
from cv_compiler.llm import LLMConfig, ManualProvider, NoopProvider, OpenAIProvider
from cv_compiler.llm.config import read_env_file, upsert_env_value
from cv_compiler.parse.loaders import load_canonical_data, load_job_spec
from cv_compiler.pipeline import BuildRequest, build_cv
from cv_compiler.render.types import RenderFormat
from cv_compiler.select.selector import select_content
from cv_compiler.types import LintIssue, Severity


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
        "--job",
        type=str,
        default=None,
        help=(
            "Path to a job description (e.g. jobs/acme.md). "
            "Use --job false to force a generic CV."
        ),
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
    build.add_argument(
        "--debug",
        action="store_true",
        help="Show debug-only warnings (e.g., non-ASCII characters).",
    )

    lint = sub.add_parser("lint", help="Validate schema and enforce ATS constraints.")
    lint_inputs = lint.add_mutually_exclusive_group()
    lint_inputs.add_argument(
        "--data", type=str, default=None, help="Path to canonical data directory."
    )
    lint_inputs.add_argument(
        "--example", type=str, default=None, help="Use a bundled example dataset by name."
    )
    lint.add_argument(
        "--debug",
        action="store_true",
        help="Show debug-only warnings (e.g., non-ASCII characters).",
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

    ingest = sub.add_parser(
        "to_mds_from_pdf", help="Extract a PDF CV into canonical Markdown files."
    )
    ingest.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to canonical data directory (default: ./data).",
    )
    ingest.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Path to the PDF CV (default: <data>/cv.pdf).",
    )
    ingest.add_argument(
        "--llm",
        type=str,
        default="openai",
        help="LLM provider for structuring the PDF text (default: openai).",
    )
    ingest.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing markdown files in the data directory.",
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


def _resolve_job_paths(
    job_arg: str | None,
    *,
    jobs_dir: Path = Path("jobs"),
) -> tuple[Path | None, ...]:
    if job_arg:
        normalized = job_arg.strip().lower()
        if normalized in {"false", "none", "no"}:
            return (None,)
        return (Path(job_arg),)
    if jobs_dir.exists():
        job_paths = sorted(
            path
            for path in jobs_dir.glob("*.md")
            if path.name.lower() != "readme.md"
        )
        if job_paths:
            return tuple(job_paths)
    return (None,)


def _filter_warnings(
    issues: Sequence[LintIssue],
    *,
    debug: bool,
) -> tuple[LintIssue, ...]:
    if debug:
        return tuple(issues)
    suppressed = {"UNICODE_NON_ASCII"}
    return tuple(issue for issue in issues if issue.code not in suppressed)


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
                            skills_request_path=out_dir / "llm_skills_request.json",
                            skills_response_path=out_dir / "llm_skills_response.json",
                            model=model,
                            base_url=base_url,
                        )
                else:
                    print(
                        f"Unknown/unsupported LLM provider: {args.llm!r} (supported: openai, noop)",
                        file=sys.stderr,
                    )
                    return 2

            job_paths = _resolve_job_paths(args.job)
            all_outputs: list[Path] = []
            had_errors = False
            for job_path in job_paths:
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
                    had_errors = True
                    continue

                errors = [i for i in result.issues if i.severity == Severity.ERROR]
                display_issues = _filter_warnings(result.issues, debug=args.debug)
                for issue in display_issues:
                    where = f" ({issue.source_path})" if issue.source_path else ""
                    print(
                        f"{issue.severity.value.upper()} {issue.code}: {issue.message}{where}",
                        file=sys.stderr,
                    )
                if errors:
                    had_errors = True
                    continue

                all_outputs.append(result.output_path)

            for path in all_outputs:
                print(path)
            return 1 if had_errors else 0
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
            display_issues = _filter_warnings(issues, debug=args.debug)
            for issue in display_issues:
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
        case "to_mds_from_pdf":
            data_dir = Path(args.data) if args.data else Path("data")
            pdf_path = Path(args.pdf) if args.pdf else data_dir / "cv.pdf"
            if not pdf_path.exists():
                print(f"PDF not found: {pdf_path}", file=sys.stderr)
                return 2

            if args.llm != "openai":
                print(
                    f"Unsupported LLM provider for ingestion: {args.llm!r} (supported: openai)",
                    file=sys.stderr,
                )
                return 2

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
                llm_config = config
                model = config.model
                base_url = config.base_url
            else:
                file_values = read_env_file(env_path)
                llm_config = None
                model = (
                    os.getenv("CV_LLM_MODEL") or file_values.get("CV_LLM_MODEL") or "manual"
                )
                base_url = os.getenv("CV_LLM_BASE_URL") or file_values.get("CV_LLM_BASE_URL")

            try:
                result = ingest_pdf_to_markdown(
                    data_dir=data_dir,
                    pdf_path=pdf_path,
                    llm_mode=mode,
                    llm_config=llm_config,
                    overwrite=args.overwrite,
                    request_path=data_dir / "llm_ingest_request.json",
                    response_path=data_dir / "llm_ingest_response.json",
                    manual_model=model,
                    manual_base_url=base_url,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"PDF ingestion failed: {exc}", file=sys.stderr)
                return 1

            for warning in result.warnings:
                print(f"WARNING INGEST: {warning}", file=sys.stderr)

            for path in result.written_paths:
                print(path)
            return 0
        case _:
            parser.error(f"Unknown command: {args.command}")
            return 2
