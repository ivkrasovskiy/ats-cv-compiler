"""
Lint interfaces for inputs and outputs.

Provides hooks to validate canonical data and to check rendered artifacts against ATS constraints.
Implementation is currently stubbed.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from cv_compiler.schema.models import CanonicalData
from cv_compiler.types import LintIssue, Severity


def lint_build_inputs(data: CanonicalData) -> Sequence[LintIssue]:
    """Validate canonical data (schema + content constraints)."""
    issues: list[LintIssue] = []

    def iter_ids() -> Iterable[tuple[str, Path | None]]:
        yield data.profile.id, data.profile.source_path
        yield data.skills.id, data.skills.source_path
        if data.education is not None:
            yield data.education.id, data.education.source_path
        for e in data.experience:
            yield e.id, e.source_path
        for p in data.projects:
            yield p.id, p.source_path

    seen: dict[str, Path | None] = {}
    for item_id, source_path in iter_ids():
        if item_id in seen:
            issues.append(
                LintIssue(
                    code="ID_DUPLICATE",
                    message=f"Duplicate id `{item_id}` (also seen in {seen[item_id]})",
                    severity=Severity.ERROR,
                    source_path=source_path,
                )
            )
        else:
            seen[item_id] = source_path

    def lint_text(text: str, *, source_path: Path | None, field: str) -> None:
        if "\n" in text or "\r" in text:
            issues.append(
                LintIssue(
                    code="TEXT_NEWLINE",
                    message=f"Newline not allowed in {field}",
                    severity=Severity.ERROR,
                    source_path=source_path,
                )
            )
        if "\t" in text:
            issues.append(
                LintIssue(
                    code="TEXT_TAB",
                    message=f"Tab not allowed in {field}",
                    severity=Severity.ERROR,
                    source_path=source_path,
                )
            )
        for ch in text:
            if ord(ch) > 127:
                issues.append(
                    LintIssue(
                        code="UNICODE_NON_ASCII",
                        message=f"Non-ASCII character {ch!r} in {field} (ATS risk)",
                        severity=Severity.WARNING,
                        source_path=source_path,
                    )
                )
                break

    lint_text(data.profile.about_me, source_path=data.profile.source_path, field="profile.about_me")

    for link in data.profile.links:
        if not link.url:
            issues.append(
                LintIssue(
                    code="PROFILE_LINK_URL_MISSING",
                    message="Profile link is missing a URL; it will be skipped.",
                    severity=Severity.WARNING,
                    source_path=data.profile.source_path,
                )
            )

    for e in data.experience:
        for bullet in e.bullets:
            lint_text(bullet, source_path=e.source_path, field=f"experience[{e.id}].bullets")

    for p in data.projects:
        for bullet in p.bullets:
            lint_text(bullet, source_path=p.source_path, field=f"projects[{p.id}].bullets")

    return tuple(issues)


def lint_rendered_output(output_path: Path) -> Sequence[LintIssue]:
    """Validate a rendered output artifact against ATS constraints."""
    issues: list[LintIssue] = []
    if not output_path.exists():
        issues.append(
            LintIssue(
                code="OUTPUT_MISSING",
                message=f"Missing output file: {output_path}",
                severity=Severity.ERROR,
                source_path=None,
            )
        )
        return tuple(issues)

    ext = output_path.suffix.lower()
    if ext not in {".pdf", ".md"}:
        issues.append(
            LintIssue(
                code="OUTPUT_EXT",
                message=f"Unexpected output extension: {output_path.suffix}",
                severity=Severity.WARNING,
                source_path=None,
            )
        )

    if output_path.stat().st_size == 0:
        issues.append(
            LintIssue(
                code="OUTPUT_EMPTY",
                message="Output file is empty",
                severity=Severity.ERROR,
                source_path=None,
            )
        )
    return tuple(issues)
