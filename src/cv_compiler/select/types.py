from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    item_id: str
    score: float
    matched_keywords: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SelectionResult:
    selected_experience_ids: tuple[str, ...]
    selected_project_ids: tuple[str, ...]
    decisions: tuple[SelectionDecision, ...]
