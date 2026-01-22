"""
Project file validation helpers.

Validates per-project frontmatter fields without loading the full dataset.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cv_compiler.parse.frontmatter import parse_markdown_frontmatter


@dataclass(frozen=True, slots=True)
class ProjectIssue:
    path: Path
    code: str
    message: str
    severity: str = "ERROR"


def collect_project_issues(projects_dir: Path) -> tuple[ProjectIssue, ...]:
    issues: list[ProjectIssue] = []
    if not projects_dir.exists():
        issues.append(
            ProjectIssue(
                path=projects_dir,
                code="PROJECTS_DIR_MISSING",
                message="Projects directory does not exist.",
            )
        )
        return tuple(issues)

    seen_ids: dict[str, Path] = {}
    for path in sorted(projects_dir.glob("*.md")):
        try:
            doc = parse_markdown_frontmatter(path)
        except Exception as exc:  # noqa: BLE001
            issues.append(
                ProjectIssue(
                    path=path,
                    code="FRONTMATTER_INVALID",
                    message=f"Failed to parse frontmatter: {exc}",
                )
            )
            continue

        fm = doc.frontmatter
        if not isinstance(fm, Mapping):
            issues.append(
                ProjectIssue(
                    path=path,
                    code="FRONTMATTER_MISSING",
                    message="Missing frontmatter mapping.",
                )
            )
            continue

        _check_required_str(fm, "id", path, issues)
        entry_id = fm.get("id")
        if isinstance(entry_id, str) and entry_id.strip():
            existing = seen_ids.get(entry_id)
            if existing is not None:
                issues.append(
                    ProjectIssue(
                        path=path,
                        code="PROJECT_ID_DUPLICATE",
                        message=f"Duplicate id `{entry_id}` (also in {existing}).",
                    )
                )
            else:
                seen_ids[entry_id] = path

        _check_required_str(fm, "name", path, issues)
        _check_required_list_of_str(fm, "tags", path, issues)
        _check_required_list_of_str(fm, "bullets", path, issues)
        _check_optional_str(fm, "company", path, issues)
        _check_optional_str(fm, "role", path, issues)
        _check_optional_str(fm, "start_date", path, issues)
        _check_optional_str(fm, "end_date", path, issues)

    return tuple(issues)


def _check_required_str(
    fm: Mapping[str, Any],
    key: str,
    path: Path,
    issues: list[ProjectIssue],
) -> None:
    value = fm.get(key)
    if not isinstance(value, str) or not value.strip():
        issues.append(
            ProjectIssue(
                path=path,
                code="FIELD_INVALID",
                message=f"Missing or invalid `{key}`.",
            )
        )


def _check_required_list_of_str(
    fm: Mapping[str, Any],
    key: str,
    path: Path,
    issues: list[ProjectIssue],
) -> None:
    value = fm.get(key)
    if not isinstance(value, list):
        issues.append(
            ProjectIssue(
                path=path,
                code="FIELD_INVALID",
                message=f"Missing or invalid `{key}` list.",
            )
        )
        return
    for item in value:
        if not isinstance(item, str) or not item.strip():
            issues.append(
                ProjectIssue(
                    path=path,
                    code="FIELD_INVALID",
                    message=f"Invalid `{key}` item.",
                )
            )
            return


def _check_optional_str(
    fm: Mapping[str, Any],
    key: str,
    path: Path,
    issues: list[ProjectIssue],
) -> None:
    if key not in fm:
        return
    value = fm.get(key)
    if value is None:
        return
    if not isinstance(value, str):
        issues.append(
            ProjectIssue(
                path=path,
                code="FIELD_INVALID",
                message=f"Invalid `{key}` value.",
            )
        )
