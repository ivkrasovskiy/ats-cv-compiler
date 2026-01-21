"""
Markdown rendering for CV content.

Produces a deterministic, ATS-safe Markdown representation used as the source for PDF rendering.
"""

from __future__ import annotations

from cv_compiler.schema.models import CanonicalData
from cv_compiler.select.types import SelectionResult


def build_markdown(data: CanonicalData, selection: SelectionResult) -> str:
    """Build a Markdown representation of the selected CV content."""
    lines: list[str] = []

    def add_blank() -> None:
        if lines and lines[-1] != "":
            lines.append("")

    def add_section(title: str) -> None:
        add_blank()
        lines.append(f"## {title}")

    lines.append(f"# {data.profile.name}")
    contact_parts: list[str] = [data.profile.headline, data.profile.location]
    if data.profile.email:
        contact_parts.append(data.profile.email)
    contact_parts.extend([link.url for link in data.profile.links if link.url])
    contact_line = " - ".join(part for part in contact_parts if part)
    if contact_line:
        lines.append(contact_line)

    if data.profile.about_me:
        add_section("About Me")
        lines.append(data.profile.about_me)

    selected_exp = set(selection.selected_experience_ids)
    if selected_exp:
        add_section("Experience")
        for entry in sorted(
            [e for e in data.experience if e.id in selected_exp],
            key=lambda x: (x.start_date, x.id),
            reverse=True,
        ):
            end = entry.end_date or "Present"
            location = f" ({entry.location})" if entry.location else ""
            lines.append(
                f"### {entry.title} - {entry.company}{location} | {entry.start_date} - {end}"
            )
            for bullet in entry.bullets:
                lines.append(f"- {bullet}")
            add_blank()

    selected_proj = set(selection.selected_project_ids)
    if selected_proj:
        add_section("Projects")
        for entry in sorted(
            [p for p in data.projects if p.id in selected_proj],
            key=lambda x: x.name,
        ):
            lines.append(f"### {entry.name}")
            for bullet in entry.bullets:
                lines.append(f"- {bullet}")
            add_blank()

    add_section("Skills")
    for category in data.skills.categories:
        items = ", ".join(category.items)
        lines.append(f"**{category.name}**: {items}")

    if data.education and data.education.entries:
        add_section("Education")
        for entry in data.education.entries:
            start = entry.start_date or ""
            end = entry.end_date or ""
            dates = f"{start}-{end}".strip("-")
            where = f" ({entry.location})" if entry.location else ""
            line = f"{entry.degree} - {entry.institution}{where}"
            if dates:
                line = f"{line} | {dates}"
            lines.append(f"- {line}")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"
