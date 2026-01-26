"""
Validate LLM experience drafts against canonical project data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cv_compiler.llm.experience import (
    _collect_allowed_keywords,
    _collect_allowed_numbers,
    _validate_bullet_numbers,
    _validate_keywords,
    parse_experience_drafts,
)
from cv_compiler.llm.openai import extract_chat_content
from cv_compiler.schema.models import ProjectEntry


@dataclass(frozen=True, slots=True)
class DraftIssue:
    code: str
    message: str
    severity: str = "WARNING"
    experience_id: str | None = None


def collect_draft_issues(
    *,
    draft_text: str,
    projects: tuple[ProjectEntry, ...],
) -> tuple[DraftIssue, ...]:
    issues: list[DraftIssue] = []
    try:
        drafts = parse_experience_drafts(draft_text)
    except Exception as exc:  # noqa: BLE001
        return (DraftIssue(code="DRAFT_PARSE_FAILED", message=str(exc), severity="ERROR"),)

    if len(drafts) > 5:
        issues.append(
            DraftIssue(
                code="DRAFT_TOO_MANY",
                message="LLM must produce at most 5 experiences.",
                severity="ERROR",
            )
        )

    project_by_id = {p.id: p for p in projects}
    allowed_numbers = _collect_allowed_numbers(projects)
    allowed_phrases, allowed_tokens = _collect_allowed_keywords(projects)

    for draft in drafts:
        if not draft.source_project_ids:
            issues.append(
                DraftIssue(
                    code="MISSING_SOURCE_PROJECTS",
                    message="Experience is missing source_project_ids.",
                    severity="ERROR",
                    experience_id=draft.id,
                )
            )
            continue
        src_projects: list[ProjectEntry] = []
        for pid in draft.source_project_ids:
            project = project_by_id.get(pid)
            if project is None:
                issues.append(
                    DraftIssue(
                        code="UNKNOWN_PROJECT_ID",
                        message=f"Unknown project id {pid!r}.",
                        severity="ERROR",
                        experience_id=draft.id,
                    )
                )
            else:
                src_projects.append(project)
        if not src_projects:
            continue

        company_set = {p.company for p in src_projects if p.company}
        if len(company_set) != 1:
            issues.append(
                DraftIssue(
                    code="COMPANY_MISMATCH",
                    message="Experience references projects with multiple companies.",
                    severity="ERROR",
                    experience_id=draft.id,
                )
            )

        start_dates = [p.start_date for p in src_projects if p.start_date]
        if not start_dates:
            issues.append(
                DraftIssue(
                    code="MISSING_START_DATE",
                    message="Experience references projects missing start_date.",
                    severity="ERROR",
                    experience_id=draft.id,
                )
            )

        role_set = {p.role for p in src_projects if p.role}
        if not role_set and not draft.role:
            issues.append(
                DraftIssue(
                    code="MISSING_ROLE",
                    message="No role available in project data or draft.",
                    experience_id=draft.id,
                )
            )

        warnings: list[str] = []
        for bullet in draft.bullets:
            _validate_bullet_numbers(bullet, allowed_numbers, warnings=warnings)
        _validate_keywords(
            draft.keywords,
            allowed_phrases=allowed_phrases,
            allowed_tokens=allowed_tokens,
            warnings=warnings,
            exp_id=draft.id,
        )
        for warning in warnings:
            issues.append(
                DraftIssue(
                    code="DRAFT_WARNING",
                    message=warning,
                    experience_id=draft.id,
                )
            )

    return tuple(issues)


def load_draft_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    content = extract_chat_content(parsed)
    if content is not None:
        return content
    if isinstance(parsed, dict) and "experiences" in parsed:
        return raw
    direct = parsed.get("content") if isinstance(parsed, dict) else None
    if isinstance(direct, str):
        return direct
    return raw
