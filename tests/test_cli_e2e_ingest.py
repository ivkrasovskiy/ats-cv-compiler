"""
E2E tests for CLI-backed PDF ingest — gemini and claude paths.

Each test:
  1. Creates a real PDF with extractable text (fpdf2, no mocking)
  2. Spawns a fake CLI subprocess (an executable Python script)
  3. Runs the full ingest pipeline end-to-end via ingest_pdf_to_markdown
  4. Asserts files were written AND the subprocess received the right inputs

Gemini contract: prompt passed as CLI arg, GEMINI_MODEL env var set.
Claude contract: prompt passed via stdin, GEMINI_MODEL NOT injected.

subprocess.run is never mocked — these are real subprocess invocations.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from cv_compiler.ingest.pdf_ingest import ingest_pdf_to_markdown
from cv_compiler.llm.codex import CodexExecConfig

_ROOT = Path(__file__).resolve().parents[1]

# Minimal valid JSON that parse_ingest_response accepts
_RESPONSE = json.dumps(
    {
        "profile": {
            "name": "Test User",
            "headline": "Engineer",
            "location": "Remote",
            "email": "test@example.com",
            "links": [],
            "about_me": "An experienced engineer who builds reliable systems.",
        },
        "experience": [],
        "projects": [],
        "skills": [{"name": "Languages", "items": ["Python"]}],
        "education": [],
    }
)

# CV text long enough to pass the 200 non-whitespace char minimum
_CV_TEXT = "Jordan Blake Senior Backend Engineer San Francisco CA Remote " * 6


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_pdf(path: Path) -> None:
    """Create a minimal real PDF with extractable text using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, _CV_TEXT)
    pdf.output(str(path))


def _make_prompt(path: Path) -> None:
    """Write a minimal prompt file — keeps CLI args small."""
    path.write_text("Extract CV info from: {{PDF_TEXT}}", encoding="utf-8")


def _make_cli(path: Path, *, log: Path, mode: str) -> Path:
    """
    Write a fake CLI executable.

    mode='gemini': receives prompt as arg, writes GEMINI_MODEL env var to log.
    mode='claude': receives prompt from stdin, writes stdin byte count to log.

    Both exit 0 and print the valid JSON response on stdout.
    """
    log_repr = repr(str(log))
    response_repr = repr(_RESPONSE)

    if mode == "gemini":
        body = (
            "import os, sys\n"
            f"with open({log_repr}, 'w') as f:\n"
            "    f.write(os.environ.get('GEMINI_MODEL', 'NOT_SET'))\n"
            f"print({response_repr})\n"
        )
    else:  # claude — prompt arrives on stdin
        body = (
            "import sys\n"
            "data = sys.stdin.read()\n"
            f"with open({log_repr}, 'w') as f:\n"
            "    f.write(str(len(data)))\n"
            f"print({response_repr})\n"
        )

    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _gemini_config(cli: Path) -> CodexExecConfig:
    return CodexExecConfig(
        command=str(cli),
        args=("-p",),
        model="gemini-2.0-flash",
        timeout_seconds=10,
        prompt_mode="arg",
        progress=False,
    )


def _claude_config(cli: Path) -> CodexExecConfig:
    return CodexExecConfig(
        command=str(cli),
        args=("-p",),
        model=None,
        timeout_seconds=10,
        prompt_mode="stdin",
        progress=False,
    )


# ── §1-3 gemini path ───────────────────────────────────────────────────────────


def test_gemini_cli_produces_ingest_files(tmp_path):
    pdf, prompt = tmp_path / "cv.pdf", tmp_path / "prompt.md"
    _make_pdf(pdf)
    _make_prompt(prompt)
    cli = _make_cli(tmp_path / "fake_gemini.py", log=tmp_path / "model.log", mode="gemini")

    result = ingest_pdf_to_markdown(
        data_dir=tmp_path / "data",
        pdf_path=pdf,
        llm_mode="cli",
        codex_config=_gemini_config(cli),
        prompt_path=prompt,
    )

    assert (tmp_path / "data" / "profile.md").exists()
    assert any(p.name == "profile.md" for p in result.written_paths)


def test_gemini_cli_passes_model_env_var(tmp_path):
    pdf, prompt = tmp_path / "cv.pdf", tmp_path / "prompt.md"
    _make_pdf(pdf)
    _make_prompt(prompt)
    log = tmp_path / "model.log"
    cli = _make_cli(tmp_path / "fake_gemini.py", log=log, mode="gemini")

    ingest_pdf_to_markdown(
        data_dir=tmp_path / "data",
        pdf_path=pdf,
        llm_mode="cli",
        codex_config=_gemini_config(cli),
        prompt_path=prompt,
    )

    assert log.read_text(encoding="utf-8") == "gemini-2.0-flash"


def test_gemini_without_model_does_not_inject_env_var(tmp_path):
    """When config.model is None, GEMINI_MODEL must not appear in the subprocess env."""
    pdf, prompt = tmp_path / "cv.pdf", tmp_path / "prompt.md"
    _make_pdf(pdf)
    _make_prompt(prompt)
    log = tmp_path / "model.log"
    cli = _make_cli(tmp_path / "fake_gemini.py", log=log, mode="gemini")

    config = CodexExecConfig(
        command=str(cli),
        args=("-p",),
        model=None,
        timeout_seconds=10,
        prompt_mode="arg",
        progress=False,
    )

    # Ensure GEMINI_MODEL is absent from the parent process env
    saved = os.environ.pop("GEMINI_MODEL", None)
    try:
        ingest_pdf_to_markdown(
            data_dir=tmp_path / "data",
            pdf_path=pdf,
            llm_mode="cli",
            codex_config=config,
            prompt_path=prompt,
        )
    finally:
        if saved is not None:
            os.environ["GEMINI_MODEL"] = saved

    assert log.read_text(encoding="utf-8") == "NOT_SET"


# ── §4-5 claude path ───────────────────────────────────────────────────────────


def test_claude_cli_produces_ingest_files(tmp_path):
    pdf, prompt = tmp_path / "cv.pdf", tmp_path / "prompt.md"
    _make_pdf(pdf)
    _make_prompt(prompt)
    cli = _make_cli(tmp_path / "fake_claude.py", log=tmp_path / "stdin.log", mode="claude")

    result = ingest_pdf_to_markdown(
        data_dir=tmp_path / "data",
        pdf_path=pdf,
        llm_mode="cli",
        codex_config=_claude_config(cli),
        prompt_path=prompt,
    )

    assert (tmp_path / "data" / "profile.md").exists()
    assert any(p.name == "profile.md" for p in result.written_paths)


def test_claude_cli_receives_prompt_via_stdin(tmp_path):
    """Claude path must deliver the full prompt over stdin, not as a CLI argument."""
    pdf, prompt = tmp_path / "cv.pdf", tmp_path / "prompt.md"
    _make_pdf(pdf)
    _make_prompt(prompt)
    log = tmp_path / "stdin.log"
    cli = _make_cli(tmp_path / "fake_claude.py", log=log, mode="claude")

    ingest_pdf_to_markdown(
        data_dir=tmp_path / "data",
        pdf_path=pdf,
        llm_mode="cli",
        codex_config=_claude_config(cli),
        prompt_path=prompt,
    )

    stdin_bytes = int(log.read_text(encoding="utf-8"))
    assert stdin_bytes > 0  # non-empty prompt was sent via stdin
