"""Shared helpers for parsing single-field JSON responses from LLM providers."""

from __future__ import annotations

import json


def parse_json_field(text: str, field: str, label: str) -> str:
    """Parse a JSON object and return a single non-empty string field.

    Args:
        text:  Raw text output from the LLM.
        field: Key to extract (e.g. ``"summary"`` or ``"cover_letter"``).
        label: Human-readable name used in error messages (e.g. ``"Experience summary"``).

    Returns:
        The stripped string value of ``field``.

    Raises:
        ValueError: If the JSON is invalid, not an object, or the field is missing/empty.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} response must be a JSON object")
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must include a non-empty {field!r} field")
    return value.strip()


def make_json_schema(name: str, field: str) -> dict[str, object]:
    """Build an OpenAI JSON schema for a single string field response."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [field],
                "properties": {field: {"type": "string"}},
            },
        },
    }
