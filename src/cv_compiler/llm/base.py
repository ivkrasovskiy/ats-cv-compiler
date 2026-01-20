"""
Optional LLM provider protocol and request types.

Defines a minimal interface for constrained bullet rewriting. Implementations must not invent facts
and must keep rewrites attributable to the input items.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from cv_compiler.schema.models import JobSpec, ProjectEntry


@dataclass(frozen=True, slots=True)
class BulletRewriteRequest:
    item_id: str
    bullets: tuple[str, ...]
    job_keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BulletRewriteResult:
    item_id: str
    bullets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperienceDraft:
    id: str
    role: str | None
    bullets: tuple[str, ...]
    source_project_ids: tuple[str, ...]


class LLMProvider(Protocol):
    """
    Optional LLM provider interface.

    Implementations MUST NOT invent facts; rewrites must be attributable to the input bullets.
    """

    name: str

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]: ...

    def generate_experience(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> Sequence[ExperienceDraft]: ...


@dataclass(frozen=True, slots=True)
class NoopProvider:
    name: str = "noop"

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]:
        _ = instructions
        return [BulletRewriteResult(item_id=item.item_id, bullets=item.bullets) for item in items]

    def generate_experience(
        self,
        projects: Sequence[ProjectEntry],
        job: JobSpec | None,
    ) -> Sequence[ExperienceDraft]:
        _ = (projects, job)
        return []
