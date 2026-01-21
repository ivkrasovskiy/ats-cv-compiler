"""
Markdown rendering for CV content.

Produces a deterministic, ATS-safe Markdown representation used as the source for PDF rendering.
"""

from __future__ import annotations

import unicodedata

from cv_compiler.schema.models import CanonicalData
from cv_compiler.select.types import SelectionResult

_TRANSLATE_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2011": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "-",
        "\u00b7": "-",
    }
)


def normalize_markdown_text(text: str) -> str:
    """Normalize Unicode punctuation to ASCII for ATS-safe rendering."""
    replaced = text.translate(_TRANSLATE_MAP)
    normalized = unicodedata.normalize("NFKD", replaced)
    return normalized.encode("ascii", "ignore").decode("ascii")


def build_markdown(
    data: CanonicalData,
    selection: SelectionResult,
    highlighted_skills: tuple[str, ...] = (),
) -> str:
    """Build a Markdown representation of the selected CV content."""
    lines: list[str] = []

    def add_line(text: str) -> None:
        lines.append(normalize_markdown_text(text))

    def add_blank() -> None:
        if lines and lines[-1] != "":
            lines.append("")

    def add_section(title: str) -> None:
        add_blank()
        add_line(f"## {title}")

    add_line(f"# {data.profile.name}")
    contact_parts: list[str] = [data.profile.headline, data.profile.location]
    if data.profile.email:
        contact_parts.append(data.profile.email)
    contact_parts.extend([link.url for link in data.profile.links if link.url])
    contact_line = " - ".join(part for part in contact_parts if part)
    if contact_line:
        add_line(contact_line)

    if data.profile.about_me:
        add_section("About Me")
        add_line(data.profile.about_me)

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
            add_line(f"### {entry.title} - {entry.company}{location} | {entry.start_date} - {end}")
            for bullet in entry.bullets:
                add_line(f"- {bullet}")
            add_blank()

    selected_proj = set(selection.selected_project_ids)
    if selected_proj:
        add_section("Projects")
        for entry in sorted(
            [p for p in data.projects if p.id in selected_proj],
            key=lambda x: x.name,
        ):
            add_line(f"### {entry.name}")
            for bullet in entry.bullets:
                add_line(f"- {bullet}")
            add_blank()

    add_section("Skills")
    highlight_set = {item.strip().lower() for item in highlighted_skills if item.strip()}
    for category in data.skills.categories:
        formatted_items: list[str] = []
        for item in category.items:
            if item.strip().lower() in highlight_set:
                formatted_items.append(f"**{item}**")
            else:
                formatted_items.append(item)
        items = ", ".join(formatted_items)
        add_line(f"**{category.name}**: {items}")

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
            add_line(f"- {line}")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"
