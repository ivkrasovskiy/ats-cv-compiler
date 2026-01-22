"""
Markdown rendering for CV content.

Produces a deterministic, ATS-safe Markdown representation used as the source for PDF rendering.
"""

from __future__ import annotations

import re
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

_NUM_TOKEN_RE = re.compile(
    r"\d+(?:[.,]\d+)?(?:%|[kKmMbB])?(?:\+)?(?:-\d+(?:[.,]\d+)?(?:%|[kKmMbB])?)?"
)
_VERB_KEYWORDS = (
    "led",
    "mentored",
    "oversaw",
    "built",
    "designed",
    "implemented",
    "improved",
    "increased",
    "reduced",
    "delivered",
    "shipped",
    "developed",
    "optimized",
    "automated",
    "collaborated",
    "launched",
    "owned",
    "drove",
    "scaled",
    "trained",
    "deployed",
)


def normalize_markdown_text(text: str) -> str:
    """Normalize Unicode punctuation to ASCII for ATS-safe rendering."""
    replaced = text.translate(_TRANSLATE_MAP)
    normalized = unicodedata.normalize("NFKD", replaced)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = _fix_spacing(ascii_text)
    return re.sub(r"[ \t]{2,}", " ", ascii_text)


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
        if lines:
            while lines and lines[-1] == "":
                lines.pop()
            add_line("---")
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
                add_line(f"- {_emphasize_experience_bullet(bullet)}")
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

    if data.education and (data.education.entries or data.education.languages):
        add_section("Education and Languages")
        for entry in data.education.entries:
            start = entry.start_date or ""
            end = entry.end_date or ""
            dates = f"{start}-{end}".strip("-")
            where = f" ({entry.location})" if entry.location else ""
            line = f"{entry.degree} - {entry.institution}{where}"
            if dates:
                line = f"{line} | {dates}"
            add_line(f"- {line}")
        if data.education.languages:
            languages = ", ".join(data.education.languages)
            add_line(f"- Languages: {languages}")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def _emphasize_experience_bullet(text: str) -> str:
    if "**" in text:
        return text
    if _NUM_TOKEN_RE.search(text):
        return _bold_numeric_tokens(text)
    return _bold_first_keyword(text)


def _first_clause_end(text: str) -> int:
    for token in [",", ";", " - ", " — ", ". "]:
        idx = text.find(token)
        if idx > 0:
            return idx
    words = text.split()
    if len(words) <= 6:
        return len(text)
    snippet = " ".join(words[:6])
    return len(snippet)


def _bold_numeric_tokens(text: str) -> str:
    parts: list[str] = []
    last = 0
    for match in _NUM_TOKEN_RE.finditer(text):
        start, end = match.span()
        parts.append(text[last:start])
        parts.append(f"**{match.group(0)}**")
        last = end
    parts.append(text[last:])
    return "".join(parts)


def _bold_first_keyword(text: str) -> str:
    for verb in _VERB_KEYWORDS:
        pattern = re.compile(rf"\b{re.escape(verb)}\b", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            start, end = match.span()
            return f"{text[:start]}**{text[start:end]}**{text[end:]}"
    return text


def _fix_spacing(text: str) -> str:
    return re.sub(r"([A-Za-z])(\d)", r"\\1 \\2", text)
