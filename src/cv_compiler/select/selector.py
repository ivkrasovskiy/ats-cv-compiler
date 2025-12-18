"""
Deterministic selection interface.

Given canonical data and an optional job spec, produces a stable selection result and traceable
decision records. Implementation is currently stubbed.
"""

from __future__ import annotations

import re

from cv_compiler.schema.models import CanonicalData, JobSpec
from cv_compiler.select.types import SelectionDecision, SelectionResult

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#-]*")


def _tokenize(text: str) -> set[str]:
    return {m.group(0) for m in _TOKEN_RE.finditer(text.lower())}


def _parse_ym(s: str) -> tuple[int, int] | None:
    m = re.fullmatch(r"(\d{4})-(\d{2})", s.strip())
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    if not (1 <= month <= 12):
        return None
    return year, month


def _recency_score(start_date: str) -> float:
    parsed = _parse_ym(start_date)
    if parsed is None:
        return 0.0
    year, month = parsed
    return year * 12 + month


def _job_keywords(job: JobSpec) -> tuple[str, ...]:
    kws = set(job.keywords)
    kws.update(_tokenize(job.raw_text))
    normalized = sorted({k.strip().lower() for k in kws if k and k.strip()})
    return tuple(normalized)


def select_content(data: CanonicalData, job: JobSpec | None) -> SelectionResult:
    """
    Deterministically select which items to include in the CV.

    If `job` is None, selection should still be deterministic and produce a reasonable generic CV.
    """
    experiences = list(data.experience)
    projects = list(data.projects)

    if job is None:
        exp_ids = tuple(
            e.id for e in sorted(experiences, key=lambda e: (-_recency_score(e.start_date), e.id))
        )
        proj_ids = tuple(p.id for p in sorted(projects, key=lambda p: p.id))
        decisions = tuple(
            SelectionDecision(
                item_id=item_id, score=0.0, matched_keywords=(), reasons=("generic build",)
            )
            for item_id in (*exp_ids, *proj_ids)
        )
        return SelectionResult(
            selected_experience_ids=exp_ids,
            selected_project_ids=proj_ids,
            decisions=decisions,
        )

    keywords = _job_keywords(job)
    keyword_set = set(keywords)

    decisions: list[SelectionDecision] = []

    exp_scored: list[tuple[float, float, str, tuple[str, ...], tuple[str, ...]]] = []
    for e in experiences:
        tag_tokens = {t.strip().lower() for t in e.tags if t.strip()}
        text_tokens = _tokenize(" ".join(e.bullets) + f" {e.company} {e.title}")
        matched = sorted(keyword_set.intersection(tag_tokens.union(text_tokens)))
        tag_matches = len(keyword_set.intersection(tag_tokens))
        text_matches = len(keyword_set.intersection(text_tokens))
        score = tag_matches * 2.0 + text_matches * 1.0 + _recency_score(e.start_date) * 0.001
        reasons = (f"tag_matches={tag_matches}", f"text_matches={text_matches}")
        exp_scored.append((score, _recency_score(e.start_date), e.id, tuple(matched), reasons))

    proj_scored: list[tuple[float, str, tuple[str, ...], tuple[str, ...]]] = []
    for p in projects:
        tag_tokens = {t.strip().lower() for t in p.tags if isinstance(t, str)}
        text_tokens = _tokenize(" ".join(p.bullets) + f" {p.name}")
        matched = sorted(keyword_set.intersection(tag_tokens.union(text_tokens)))
        tag_matches = len(keyword_set.intersection(tag_tokens))
        text_matches = len(keyword_set.intersection(text_tokens))
        score = tag_matches * 2.0 + text_matches * 1.0
        reasons = (f"tag_matches={tag_matches}", f"text_matches={text_matches}")
        proj_scored.append((score, p.id, tuple(matched), reasons))

    exp_scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    proj_scored.sort(key=lambda t: (-t[0], t[1]))

    selected_experience_ids = tuple(t[2] for t in exp_scored[:3] if t[0] > 0) or tuple(
        t[2] for t in exp_scored[:1]
    )
    selected_project_ids = tuple(t[1] for t in proj_scored[:2] if t[0] > 0) or tuple(
        t[1] for t in proj_scored[:1]
    )

    for score, _, item_id, matched, reasons in exp_scored:
        decisions.append(
            SelectionDecision(
                item_id=item_id,
                score=score,
                matched_keywords=matched,
                reasons=reasons,
            )
        )
    for score, item_id, matched, reasons in proj_scored:
        decisions.append(
            SelectionDecision(
                item_id=item_id,
                score=score,
                matched_keywords=matched,
                reasons=reasons,
            )
        )

    return SelectionResult(
        selected_experience_ids=selected_experience_ids,
        selected_project_ids=selected_project_ids,
        decisions=tuple(decisions),
    )
