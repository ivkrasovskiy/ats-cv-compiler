"""
LLM configuration (optional).

The MVP does not require an LLM. When enabled, an LLM is used only for constrained rewriting of
already-selected bullets and must follow strict non-fabrication rules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 300

    @staticmethod
    def from_env(
        *,
        prefix: str = "CV_LLM_",
        env_path: Path | None = Path("config/llm.env"),
    ) -> LLMConfig | None:
        file_values = read_env_file(env_path) if env_path else {}
        base_url = os.getenv(f"{prefix}BASE_URL") or file_values.get(f"{prefix}BASE_URL")
        model = os.getenv(f"{prefix}MODEL") or file_values.get(f"{prefix}MODEL")
        if not base_url or not model:
            return None
        api_key = os.getenv(f"{prefix}API_KEY") or file_values.get(f"{prefix}API_KEY")
        timeout_raw = os.getenv(f"{prefix}TIMEOUT_SECONDS") or file_values.get(
            f"{prefix}TIMEOUT_SECONDS"
        )
        timeout = _parse_timeout(timeout_raw) if timeout_raw else 300
        return LLMConfig(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout,
        )


def read_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def upsert_env_value(path: Path, key: str, value: str) -> None:
    values = read_env_file(path)
    values[key] = value
    lines = [f"{k}={v}" for k, v in sorted(values.items())]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_timeout(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        return 300
    return value if value > 0 else 300
