"""
Diagnostic checks for the cv-compiler setup.

Checks prerequisites, data files, config, and data validity.
Run via: uv run cv doctor
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def run_doctor(cwd: Path = Path(".")) -> int:
    """Run all diagnostic checks. Returns 0 if all pass, 1 if any fail."""
    data_dir = cwd / "data"
    failed = False

    def ok(msg: str) -> None:
        print(f"[✓] {msg}")

    def fail(msg: str, fix: str) -> None:
        nonlocal failed
        failed = True
        print(f"[✗] {msg}")
        print(f"    → Fix: {fix}")

    # 1. Python >= 3.11
    vi = sys.version_info
    if vi >= (3, 11):
        ok(f"Python {vi.major}.{vi.minor}.{vi.micro}")
    else:
        fail(
            f"Python 3.11+ required (found {vi.major}.{vi.minor})",
            "Install from https://www.python.org/downloads/",
        )

    # 2. uv on PATH
    if shutil.which("uv"):
        ok("uv found")
    else:
        fail(
            "uv not found on PATH",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
        )

    # 3. claude on PATH
    if shutil.which("claude"):
        ok("claude found")
    else:
        fail(
            "claude not found on PATH",
            "npm install -g @anthropic-ai/claude-code",
        )

    # 4. data/ exists
    if not data_dir.is_dir():
        fail(
            "data/ directory not found",
            "cp -r examples/basic/data data",
        )
        # Skip remaining data checks — nothing to check
        return 1

    ok("data/ directory exists")

    # 5. data/profile.md
    profile_path = data_dir / "profile.md"
    if not profile_path.exists():
        fail("data/profile.md not found", "cp examples/basic/data/profile.md data/profile.md")
    else:
        ok("data/profile.md exists")

    # 6. data/skills.md
    skills_path = data_dir / "skills.md"
    if not skills_path.exists():
        fail("data/skills.md not found", "cp examples/basic/data/skills.md data/skills.md")
    else:
        ok("data/skills.md exists")

    # 7. data/education.md
    education_path = data_dir / "education.md"
    if not education_path.exists():
        fail(
            "data/education.md not found",
            "cp examples/basic/data/education.md data/education.md",
        )
    else:
        ok("data/education.md exists")

    # 8. data/experience/ non-empty
    experience_dir = data_dir / "experience"
    if not experience_dir.is_dir() or not list(experience_dir.glob("*.md")):
        fail(
            "data/experience/ is empty or missing",
            "cp -r examples/basic/data/experience data/experience",
        )
    else:
        count = len(list(experience_dir.glob("*.md")))
        ok(f"data/experience/ has {count} file(s)")

    # 9. data/projects/ non-empty
    projects_dir = data_dir / "projects"
    if not projects_dir.is_dir() or not list(projects_dir.glob("*.md")):
        fail(
            "data/projects/ is empty or missing",
            "cp -r examples/basic/data/projects data/projects",
        )
    else:
        count = len(list(projects_dir.glob("*.md")))
        ok(f"data/projects/ has {count} file(s)")

    # 10. YAML schema valid (only if required files exist)
    if profile_path.exists() and skills_path.exists():
        try:
            from cv_compiler.parse.loaders import load_canonical_data

            data = load_canonical_data(data_dir)
            ok("YAML schema valid")
        except Exception as exc:  # noqa: BLE001
            fail(f"YAML parse error: {exc}", "Fix the reported file and re-run cv doctor")
            return 1

        # 11. Lint passes
        try:
            from cv_compiler.lint.linter import lint_build_inputs
            from cv_compiler.types import Severity

            issues = lint_build_inputs(data)
            errors = [i for i in issues if i.severity == Severity.ERROR]
            warnings = [i for i in issues if i.severity == Severity.WARNING]
            if errors:
                for issue in errors:
                    where = f" ({issue.source_path})" if issue.source_path else ""
                    fail(
                        f"Lint error {issue.code}: {issue.message}{where}",
                        "Fix the reported file and re-run cv doctor",
                    )
            else:
                if warnings:
                    ok(f"Lint passed ({len(warnings)} warning(s))")
                    for issue in warnings:
                        where = f" ({issue.source_path})" if issue.source_path else ""
                        print(f"    [!] {issue.code}: {issue.message}{where}")
                else:
                    ok("Lint passed")
        except Exception as exc:  # noqa: BLE001
            fail(f"Lint check failed: {exc}", "Run: uv run cv lint")

    if failed:
        print("\nSome checks failed. Fix the issues above and re-run: uv run cv doctor")
        return 1

    print("\nAll checks passed. Ready to build: uv run cv build --job false")
    return 0
