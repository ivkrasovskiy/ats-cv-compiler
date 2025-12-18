from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BulletRewriteRequest:
    item_id: str
    bullets: tuple[str, ...]
    job_keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BulletRewriteResult:
    item_id: str
    bullets: tuple[str, ...]


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


@dataclass(frozen=True, slots=True)
class NoopProvider:
    name: str = "noop"

    def rewrite_bullets(
        self,
        items: Sequence[BulletRewriteRequest],
        instructions: str | None,
    ) -> Sequence[BulletRewriteResult]:
        raise NotImplementedError
