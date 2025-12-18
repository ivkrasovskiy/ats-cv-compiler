"""
Formatting helpers for selection explanations.

Used by `cv explain` to turn structured selection results into a human-readable report.
Implementation is scaffolded and will be filled in alongside selection logic.
"""

from __future__ import annotations

from cv_compiler.select.types import SelectionResult


def format_selection_explanation(selection: SelectionResult) -> str:
    """Format a human-readable explanation for `cv explain`."""
    selected_exp = set(selection.selected_experience_ids)
    selected_proj = set(selection.selected_project_ids)

    lines: list[str] = []
    lines.append("Selection decisions:")
    lines.append("")
    for decision in sorted(selection.decisions, key=lambda d: (-d.score, d.item_id)):
        included = decision.item_id in selected_exp or decision.item_id in selected_proj
        flag = "IN" if included else "OUT"
        matched = ", ".join(decision.matched_keywords) if decision.matched_keywords else "-"
        reasons = ", ".join(decision.reasons) if decision.reasons else "-"
        lines.append(
            f"- {flag} {decision.item_id} score={decision.score:.3f} matched=[{matched}] {reasons}"
        )
    lines.append("")
    return "\n".join(lines)
