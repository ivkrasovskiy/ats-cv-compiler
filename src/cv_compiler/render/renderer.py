"""
Rendering interface for CV output.

This module defines the `render_cv` entrypoint used by the pipeline to produce final artifacts.
Rendering is markdown-first to keep PDF output deterministic and editable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from cv_compiler.render.markdown import build_markdown, normalize_markdown_text
from cv_compiler.render.types import RenderFormat, RenderRequest, RenderResult


def render_cv(request: RenderRequest) -> RenderResult:
    """Render a CV using a template-driven backend."""
    output_path = request.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_path = request.markdown_path or output_path.with_suffix(".md")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(
        request.data,
        request.selection,
        highlighted_skills=request.highlighted_skills,
        skills_filter=request.skills_filter,
    )
    markdown_path.write_text(markdown, encoding="utf-8")

    pdf_path: Path | None = None
    if request.format == RenderFormat.PDF:
        render_markdown_to_pdf(markdown, output_path)
        pdf_path = output_path
        output = output_path
    else:
        output = markdown_path

    return RenderResult(output_path=output, markdown_path=markdown_path, pdf_path=pdf_path)


def render_markdown_to_pdf(markdown: str, output_path: Path) -> None:
    """Render a Markdown CV to PDF using a minimal, ATS-safe subset."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_creator("ats-cv-compiler")
    pdf.set_creation_date(datetime(2000, 1, 1, tzinfo=UTC))

    def heading(text: str) -> None:
        pdf.ln(4)
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, _normalize_pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", size=10)

    def subheading(text: str) -> None:
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _normalize_pdf_text(text))
        pdf.set_font("Helvetica", size=10)

    def paragraph(text: str, *, size: int = 10) -> None:
        _render_rich_line(pdf, text, size=size)

    def bullet(text: str) -> None:
        _render_rich_line(pdf, f"- {text}", size=10)

    seen_name = False
    seen_contact = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(2)
            continue

        if line.startswith("# "):
            title = _normalize_pdf_text(line[2:].strip())
            if title:
                pdf.set_author(title)
                pdf.set_title(f"{title} - CV")
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            seen_name = True
            seen_contact = False
            continue

        if line == "---":
            y = pdf.get_y() + 1
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(2)
            continue

        if line.startswith("## "):
            heading(line[3:].strip())
            continue

        if line.startswith("### "):
            subheading(_normalize_pdf_text(line[4:].strip()))
            continue

        if line.startswith("- "):
            bullet(line[2:].strip())
            continue

        if seen_name and not seen_contact:
            paragraph(line, size=11)
            seen_contact = True
            continue

        paragraph(line, size=10)

    pdf.output(str(output_path))


def _normalize_pdf_text(text: str) -> str:
    return normalize_markdown_text(text)


def _split_bold(text: str) -> list[tuple[str, bool]]:
    parts = text.split("**")
    segments: list[tuple[str, bool]] = []
    bold = False
    for part in parts:
        segments.append((part, bold))
        bold = not bold
    return segments


def _render_rich_line(pdf: FPDF, text: str, *, size: int) -> None:
    line_height = 5
    max_width = pdf.w - pdf.l_margin - pdf.r_margin
    tokens: list[tuple[str, bool]] = []
    for segment, is_bold in _split_bold(text):
        for word in segment.split():
            tokens.append((word, is_bold))

    line_tokens: list[tuple[str, bool]] = []
    line_width = 0.0

    for word, is_bold in tokens:
        token_text = word if not line_tokens else f" {word}"
        pdf.set_font("Helvetica", style="B" if is_bold else "", size=size)
        token_width = pdf.get_string_width(_normalize_pdf_text(token_text))
        if line_tokens and line_width + token_width > max_width:
            _write_tokens_line(pdf, line_tokens, size=size, line_height=line_height)
            line_tokens = []
            line_width = 0.0
            token_text = word
            token_width = pdf.get_string_width(_normalize_pdf_text(token_text))
        line_tokens.append((token_text, is_bold))
        line_width += token_width

    if line_tokens:
        _write_tokens_line(pdf, line_tokens, size=size, line_height=line_height)


def _write_tokens_line(
    pdf: FPDF,
    tokens: list[tuple[str, bool]],
    *,
    size: int,
    line_height: int,
) -> None:
    pdf.set_x(pdf.l_margin)
    for token_text, is_bold in tokens:
        pdf.set_font("Helvetica", style="B" if is_bold else "", size=size)
        pdf.write(line_height, _normalize_pdf_text(token_text))
    pdf.ln(line_height)
