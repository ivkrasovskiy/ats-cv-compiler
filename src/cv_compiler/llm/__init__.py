"""
Optional LLM interfaces and providers.

LLMs are helpers for rewriting/condensing already-selected bullets; they are not the source of
truth. Providers must follow strict non-fabrication constraints.
"""

from __future__ import annotations

from .base import LLMProvider, NoopProvider
from .config import LLMConfig

__all__ = ["LLMConfig", "LLMProvider", "NoopProvider"]
