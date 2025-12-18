"""
Rendering interface for CV output.

This module defines the `render_cv` entrypoint used by the pipeline to produce final artifacts.
Implementation is currently stubbed.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from cv_compiler.render.types import RenderRequest, RenderResult


def render_cv(request: RenderRequest) -> RenderResult:
    """Render a CV using a template-driven backend."""
    output_path = request.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = request.data
    selection = request.selection

    selected_exp = set(selection.selected_experience_ids)
    selected_proj = set(selection.selected_project_ids)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_creator("ats-cv-compiler")
    pdf.set_author(data.profile.name)
    pdf.set_title(f"{data.profile.name} - CV")
    pdf.set_creation_date(datetime(2000, 1, 1, tzinfo=UTC))

    def heading(text: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", size=10)

    def paragraph(text: str) -> None:
        pdf.set_font("Helvetica", size=10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, text)

    def bullets(items: tuple[str, ...]) -> None:
        pdf.set_font("Helvetica", size=10)
        for item in items:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, f"- {item}")

    pdf.set_font("Helvetica", style="B", size=16)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 8, data.profile.name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", size=11)
    contact_parts: list[str] = [data.profile.headline, data.profile.location]
    if data.profile.email:
        contact_parts.append(data.profile.email)
    contact_parts.extend([link.url for link in data.profile.links])
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, " - ".join(part for part in contact_parts if part))

    if data.profile.summary:
        heading("Summary")
        bullets(data.profile.summary)

    if selected_exp:
        heading("Experience")
        for e in sorted(
            [e for e in data.experience if e.id in selected_exp],
            key=lambda x: (x.start_date, x.id),
            reverse=True,
        ):
            pdf.set_font("Helvetica", style="B", size=11)
            end = e.end_date or "Present"
            location = f" ({e.location})" if e.location else ""
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, f"{e.title} - {e.company}{location} | {e.start_date} - {end}")
            pdf.set_font("Helvetica", size=10)
            bullets(e.bullets)

    if selected_proj:
        heading("Projects")
        for p in sorted([p for p in data.projects if p.id in selected_proj], key=lambda x: x.name):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, p.name)
            pdf.set_font("Helvetica", size=10)
            bullets(p.bullets)

    heading("Skills")
    for cat in data.skills.categories:
        pdf.set_font("Helvetica", style="B", size=10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, cat.name)
        pdf.set_font("Helvetica", size=10)
        paragraph(", ".join(cat.items))

    if data.education and data.education.entries:
        heading("Education")
        for entry in data.education.entries:
            start = entry.start_date or ""
            end = entry.end_date or ""
            dates = f"{start}-{end}".strip("-")
            where = f" ({entry.location})" if entry.location else ""
            line = f"{entry.degree} - {entry.institution}{where}"
            if dates:
                line = f"{line} | {dates}"
            paragraph(line)

    pdf.output(str(output_path))
    return RenderResult(output_path=output_path)
