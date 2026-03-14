"""
Bullet polish prompt builder and response parser for Agent 4.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from cv_compiler.llm.base import BulletRewriteRequest, BulletRewriteResult
from cv_compiler.llm.job_analysis import JobAnalysis, format_job_analysis_context

_PROMPT_PATH = Path("prompts/agents/bullet_polish_prompt.md")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?%?")


def build_bullet_polish_prompt(
    items: tuple[BulletRewriteRequest, ...],
    job_analysis: JobAnalysis | None,
    *,
    prompt_path: Path = _PROMPT_PATH,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    items_payload = [
        {
            "item_id": item.item_id,
            "bullets": list(item.bullets),
            "job_keywords": list(item.job_keywords),
        }
        for item in items
    ]
    prompt = prompt.replace("{{ITEMS}}", yaml.safe_dump(items_payload, sort_keys=False).strip())
    job_context = format_job_analysis_context(job_analysis) if job_analysis else ""
    prompt = prompt.replace("{{JOB_CONTEXT}}", job_context)
    return prompt


def parse_bullet_polish_response(
    raw: str,
    original: tuple[BulletRewriteRequest, ...],
    *,
    allowed_numbers: set[str],
    max_bullet_chars: int,
    warnings: list[str],
) -> tuple[BulletRewriteResult, ...]:
    """Parse LLM response for bullet polish. Falls back to input on parse error."""
    try:
        payload = _extract_json(raw)
        data = json.loads(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        warnings.append(f"Bullet polish parse failed ({exc}); returning input unchanged")
        return tuple(
            BulletRewriteResult(item_id=item.item_id, bullets=item.bullets) for item in original
        )

    if not isinstance(data, dict) or "items" not in data:
        warnings.append("Bullet polish response missing 'items' key; returning input unchanged")
        return tuple(
            BulletRewriteResult(item_id=item.item_id, bullets=item.bullets) for item in original
        )

    original_by_id = {item.item_id: item for item in original}
    results: list[BulletRewriteResult] = []

    for entry in data["items"]:
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("item_id") or "")
        bullets_raw = entry.get("bullets")
        if not item_id or not isinstance(bullets_raw, list):
            continue
        if item_id not in original_by_id:
            warnings.append(f"Bullet polish returned unknown item_id {item_id!r}; skipping")
            continue
        original_item = original_by_id[item_id]
        polished: list[str] = []
        for bullet in bullets_raw:
            bullet = str(bullet).strip()
            if not bullet:
                continue
            for token in _NUM_RE.findall(bullet):
                if token not in allowed_numbers:
                    warnings.append(
                        f"Bullet polish invented numeric token {token!r} in bullet: {bullet!r}"
                    )
            if len(bullet) > max_bullet_chars:
                bullet = bullet[:max_bullet_chars].rstrip()
                warnings.append(f"Bullet truncated to {max_bullet_chars} chars: {bullet!r}")
            polished.append(bullet)

        if not polished:
            warnings.append(
                f"Bullet polish returned empty bullets for {item_id!r}; using originals"
            )
            results.append(BulletRewriteResult(item_id=item_id, bullets=original_item.bullets))
        else:
            results.append(BulletRewriteResult(item_id=item_id, bullets=tuple(polished)))

    # Fill in any items missing from response
    result_ids = {r.item_id for r in results}
    for item in original:
        if item.item_id not in result_ids:
            warnings.append(f"Bullet polish missing response for {item.item_id!r}; using originals")
            results.append(BulletRewriteResult(item_id=item.item_id, bullets=item.bullets))

    return tuple(results)


def _extract_json(raw: str) -> str:
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            json.loads(snippet)
            return snippet
        except json.JSONDecodeError:
            pass
    raise ValueError("No valid JSON object found in bullet polish response")
