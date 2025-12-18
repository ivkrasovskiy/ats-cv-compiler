"""
Load canonical data and job specs from disk.

This module is responsible for turning repository files into validated in-memory models for the
pipeline. Functions are currently stubs (interfaces only).
"""

from __future__ import annotations

from pathlib import Path

from cv_compiler.schema.models import CanonicalData, JobSpec


def load_canonical_data(data_dir: Path) -> CanonicalData:
    """Load and validate canonical data from a `data/` directory."""
    raise NotImplementedError


def load_job_spec(path: Path) -> JobSpec:
    """Load a job spec from a Markdown or text file."""
    raise NotImplementedError
