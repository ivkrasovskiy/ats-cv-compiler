"""
Rendering interface for CV output.

This module defines the `render_cv` entrypoint used by the pipeline to produce final artifacts.
Rendering is markdown-first to keep PDF output deterministic and editable.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from cv_compiler.render.markdown import build_markdown, normalize_markdown_text
from cv_compiler.render.types import RenderFormat, RenderRequest, RenderResult

_URL_RE = re.compile(r"https?://\S+")


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
        experience_summary=request.experience_summary,
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
        pdf.set_font("Helvetica", size=size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            0,
            5,
            _normalize_pdf_text(text),
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def bullet(text: str) -> None:
        paragraph(f"- {text}", size=10)

    def contact_line(text: str) -> None:
        """Render the contact line with clickable hyperlinks for any URLs."""
        pdf.set_font("Helvetica", size=11)
        pdf.set_x(pdf.l_margin)
        normalized = _normalize_pdf_text(text)
        last = 0
        for m in _URL_RE.finditer(normalized):
            start, end = m.span()
            if start > last:
                pdf.write(5, normalized[last:start])
            url = m.group(0)
            pdf.set_text_color(60, 80, 200)
            pdf.write(5, url, link=url)
            pdf.set_text_color(0, 0, 0)
            last = end
        if last < len(normalized):
            pdf.write(5, normalized[last:])
        pdf.ln(5)

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
            contact_line(line)
            seen_contact = True
            continue

        paragraph(line, size=10)

    pdf.output(str(output_path))


def _normalize_pdf_text(text: str) -> str:
    return normalize_markdown_text(text)
