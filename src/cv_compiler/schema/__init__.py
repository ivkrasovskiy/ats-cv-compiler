"""
Schema models for validated CV inputs.

This package defines the canonical entity types (profile/experience/projects/skills/etc.) that are
loaded from disk and passed through selection, rendering, and linting.
"""

from __future__ import annotations

from .models import (
    CanonicalData,
    EducationEntry,
    ExperienceEntry,
    JobSpec,
    Profile,
    ProjectEntry,
    Skills,
)

__all__ = [
    "CanonicalData",
    "EducationEntry",
    "ExperienceEntry",
    "JobSpec",
    "Profile",
    "ProjectEntry",
    "Skills",
]
