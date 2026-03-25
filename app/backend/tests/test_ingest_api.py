"""Tests for /api/ingest/pdf endpoint."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

_INGEST_FN = "cv_compiler.ingest.pdf_ingest.ingest_pdf_to_markdown"


def _project_root() -> Path:
    return Path(os.environ["CV_PROJECT_ROOT"])


def _write_config(provider: str, extra: str = "") -> None:
    root = _project_root()
    cfg = root / "config" / "llm.env"
    cfg.parent.mkdir(exist_ok=True)
    cfg.write_text(f"CV_AI_PROVIDER={provider}\n{extra}")


def _place_pdf() -> None:
    pdf = _project_root() / "data" / "cv.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4 fake")


def _fake_result() -> MagicMock:
    r = MagicMock()
    r.written_paths = []
    r.warnings = []
    return r


def test_ingest_pdf_missing_file_returns_400(client: TestClient):
    """Without data/cv.pdf the endpoint returns 400."""
    response = client.post("/api/ingest/pdf")
    assert response.status_code == 400
    assert "cv.pdf" in response.json()["detail"].lower()


def test_ingest_pdf_gemini_calls_cli_with_model(client: TestClient):
    """Gemini provider: codex_config has command=gemini and model=gemini-2.0-flash."""
    _place_pdf()
    _write_config("gemini", "CV_GEMINI_MODEL=gemini-2.0-flash\n")

    with patch(_INGEST_FN, return_value=_fake_result()) as mock_ingest:
        response = client.post("/api/ingest/pdf")

    assert response.status_code == 200
    _, kwargs = mock_ingest.call_args
    codex_cfg = kwargs["codex_config"]
    assert codex_cfg.command == "gemini"
    assert codex_cfg.model == "gemini-2.0-flash"
    assert codex_cfg.prompt_mode == "arg"


def test_ingest_pdf_gemini_default_model(client: TestClient):
    """Gemini provider without explicit model defaults to gemini-2.0-flash."""
    _place_pdf()
    _write_config("gemini")

    with patch(_INGEST_FN, return_value=_fake_result()) as mock_ingest:
        response = client.post("/api/ingest/pdf")

    assert response.status_code == 200
    _, kwargs = mock_ingest.call_args
    assert kwargs["codex_config"].model == "gemini-2.0-flash"


def test_ingest_pdf_claude_uses_stdin_mode(client: TestClient):
    """Claude provider: codex_config uses stdin prompt mode, no model."""
    _place_pdf()
    _write_config("claude")

    with patch(_INGEST_FN, return_value=_fake_result()) as mock_ingest:
        response = client.post("/api/ingest/pdf")

    assert response.status_code == 200
    _, kwargs = mock_ingest.call_args
    codex_cfg = kwargs["codex_config"]
    assert codex_cfg.command == "claude"
    assert codex_cfg.prompt_mode == "stdin"
    assert codex_cfg.model is None


def test_ingest_pdf_custom_uses_api_mode(client: TestClient):
    """Custom provider: llm_config is set, codex_config is None."""
    _place_pdf()
    _write_config(
        "custom",
        "CV_LLM_BASE_URL=http://localhost:1234\nCV_LLM_MODEL=test-model\n",
    )

    with patch(_INGEST_FN, return_value=_fake_result()) as mock_ingest:
        response = client.post("/api/ingest/pdf")

    assert response.status_code == 200
    _, kwargs = mock_ingest.call_args
    assert kwargs["codex_config"] is None
    assert kwargs["llm_config"] is not None
