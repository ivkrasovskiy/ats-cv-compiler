"""
Ingestion helpers for bootstrapping canonical data.
"""

from __future__ import annotations

from .pdf_ingest import IngestResult, ingest_pdf_to_markdown

__all__ = ["IngestResult", "ingest_pdf_to_markdown"]
