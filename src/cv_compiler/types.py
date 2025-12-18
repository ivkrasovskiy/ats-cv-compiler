"""
Shared enums and lint issue types.

These types are used across the pipeline to represent validation/lint findings in a uniform way.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class LintIssue:
    code: str
    message: str
    severity: Severity
    source_path: Path | None = None
