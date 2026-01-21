"""
Optional LLM interfaces and providers.

LLMs are helpers for rewriting/condensing already-selected bullets; they are not the source of
truth. Providers must follow strict non-fabrication constraints.
"""

from __future__ import annotations

from .base import ExperienceDraft, LLMProvider, NoopProvider
from .config import LLMConfig
from .manual import ManualProvider
from .openai import OpenAIProvider

__all__ = [
    "ExperienceDraft",
    "LLMConfig",
    "LLMProvider",
    "ManualProvider",
    "NoopProvider",
    "OpenAIProvider",
]
