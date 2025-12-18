"""
LLM configuration (optional).

The MVP does not require an LLM. When enabled, an LLM is used only for constrained rewriting of
already-selected bullets and must follow strict non-fabrication rules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str | None = None

    @staticmethod
    def from_env(*, prefix: str = "CV_LLM_") -> LLMConfig | None:
        base_url = os.getenv(f"{prefix}BASE_URL")
        model = os.getenv(f"{prefix}MODEL")
        if not base_url or not model:
            return None
        api_key = os.getenv(f"{prefix}API_KEY")
        return LLMConfig(base_url=base_url, model=model, api_key=api_key)
