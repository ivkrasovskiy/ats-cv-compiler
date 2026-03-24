"""
PDF ingestion helpers for bootstrapping canonical Markdown files.

Extracts machine-readable text, uses an LLM to structure it, and writes `.md` files under data/.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from cv_compiler.llm.codex import CodexExecConfig
from cv_compiler.llm.config import LLMConfig
from cv_compiler.llm.openai import build_chat_endpoint, build_chat_payload, extract_chat_content

from .pdf_models import IngestResult, ParsedCv, ParsedExperience, ParsedProfile, ParsedSkillCategory
from .pdf_parser import parse_ingest_payload, parse_ingest_response
from .pdf_writer import write_ingest_files

__all__ = [
    "IngestResult",
    "ParsedCv",
    "ParsedExperience",
    "ParsedProfile",
    "ParsedSkillCategory",
    "extract_pdf_hyperlinks",
    "extract_pdf_text",
    "ingest_pdf_to_markdown",
    "parse_ingest_payload",
    "parse_ingest_response",
    "write_ingest_files",
]

_MIN_TEXT_CHARS = 200


def extract_pdf_text(path: Path) -> str:
    """Extract text from a machine-readable PDF or raise if none is found."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("pypdf is required for PDF ingestion. Run `uv sync`.") from exc
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text)
    combined = "\n".join(chunks).strip()
    if len(re.sub(r"\s+", "", combined)) < _MIN_TEXT_CHARS:
        raise ValueError(
            "PDF contains too little extractable text; it may be scanned. "
            "Run OCR or provide a machine-readable PDF."
        )
    return combined


def extract_pdf_hyperlinks(path: Path) -> list[str]:
    """Extract all URI hyperlinks from PDF link annotations."""
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover
        return []
    reader = PdfReader(str(path))
    urls: list[str] = []
    seen: set[str] = set()
    for page in reader.pages:
        if "/Annots" not in page:
            continue
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
            except Exception:
                continue
            if annot.get("/Subtype") != "/Link":
                continue
            action = annot.get("/A")
            if action is None:
                continue
            uri = action.get("/URI")
            if uri and isinstance(uri, str) and uri not in seen:
                seen.add(uri)
                urls.append(uri)
    return urls


def ingest_pdf_to_markdown(
    *,
    data_dir: Path,
    pdf_path: Path,
    llm_mode: str,
    llm_config: LLMConfig | None = None,
    codex_config: CodexExecConfig | None = None,
    prompt_path: Path = Path("prompts/pdf_ingest_prompt.md"),
    overwrite: bool = False,
    request_path: Path | None = None,
    response_path: Path | None = None,
    manual_model: str = "manual",
    manual_base_url: str | None = None,
) -> IngestResult:
    """Convert a PDF CV into canonical Markdown files under `data_dir`."""
    text = extract_pdf_text(pdf_path)
    hyperlinks = extract_pdf_hyperlinks(pdf_path)
    prompt = _build_ingest_prompt(prompt_path, text, hyperlinks)

    payload = build_chat_payload(manual_model, prompt, _ingest_schema())
    if llm_mode == "api":
        if llm_config is None:
            raise ValueError("Missing LLM config for API mode")
        content = _request_llm_content(llm_config, prompt)
    elif llm_mode == "cli":
        if codex_config is None:
            raise ValueError("Missing codex config for CLI mode")
        content = _cli_llm_content(codex_config, prompt)
    elif llm_mode == "offline":
        if request_path is None or response_path is None:
            raise ValueError("Offline mode requires request/response paths")
        content = _manual_llm_content(
            payload=payload,
            request_path=request_path,
            response_path=response_path,
            base_url=manual_base_url,
        )
    else:
        raise ValueError(f"Unknown LLM mode: {llm_mode}")

    parsed = parse_ingest_response(content)
    return write_ingest_files(data_dir, parsed, overwrite=overwrite)


def _build_ingest_prompt(path: Path, pdf_text: str, hyperlinks: list[str] | None = None) -> str:
    prompt = path.read_text(encoding="utf-8")
    text = pdf_text.strip()
    if hyperlinks:
        links_block = "\n\n[HYPERLINKS FOUND IN PDF ANNOTATIONS]\n"
        links_block += "\n".join(f"- {url}" for url in hyperlinks)
        text = text + links_block
    return prompt.replace("{{PDF_TEXT}}", text)


def _request_llm_content(config: LLMConfig, prompt: str) -> str:
    url = build_chat_endpoint(config.base_url)
    payload = build_chat_payload(config.model, prompt, _ingest_schema())
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    req = Request(url, data=data, headers=headers, method="POST")
    with urlopen(req, timeout=config.timeout_seconds) as resp:  # noqa: S310
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    content = extract_chat_content(parsed)
    if content is None:
        raise ValueError("Unexpected LLM response shape")
    return content


def _cli_llm_content(config: CodexExecConfig, prompt: str) -> str:
    if config.prompt_mode == "arg":
        cmd = [config.command, *config.args, prompt]
        stdin_data = None
    else:
        cmd = [config.command, *config.args]
        stdin_data = prompt.encode("utf-8")
    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            timeout=config.timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f"CLI command not found: {config.command}. Is it installed and on your PATH?"
        ) from exc
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(
            f"CLI LLM failed (exit {result.returncode}): {stderr or 'unknown error'}"
        )
    raw = result.stdout.decode("utf-8", errors="replace").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _manual_llm_content(
    *,
    payload: dict[str, object],
    request_path: Path,
    response_path: Path,
    base_url: str | None,
) -> str:
    request_bundle: dict[str, Any] = {"payload": payload}
    if base_url:
        request_bundle["endpoint"] = build_chat_endpoint(base_url)
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(request_bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not response_path.exists():
        raise ValueError(
            "Manual LLM mode: response file missing. "
            f"Paste model output into {response_path} and retry."
        )
    raw = response_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    content = extract_chat_content(parsed)
    if content is not None:
        return content
    direct = parsed.get("content") if isinstance(parsed, dict) else None
    if isinstance(direct, str):
        return direct
    return raw


def _ingest_schema() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "pdf_ingest_response",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["profile", "experience", "projects", "skills", "education"],
                "properties": {
                    "profile": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "headline", "location", "email", "links", "about_me"],
                        "properties": {
                            "name": {"type": "string"},
                            "headline": {"type": "string"},
                            "location": {"type": "string"},
                            "email": {"type": "string"},
                            "links": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["label", "url"],
                                    "properties": {
                                        "label": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                },
                            },
                            "about_me": {"type": "string"},
                        },
                    },
                    "experience": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "company", "title", "location",
                                "start_date", "end_date", "bullets", "tags",
                            ],
                            "properties": {
                                "company": {"type": "string"},
                                "title": {"type": "string"},
                                "location": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                                "bullets": {"type": "array", "items": {"type": "string"}},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "name", "company", "role",
                                "start_date", "end_date", "bullets", "tags",
                            ],
                            "properties": {
                                "name": {"type": "string"},
                                "company": {"type": "string"},
                                "role": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                                "bullets": {"type": "array", "items": {"type": "string"}},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "skills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "items"],
                            "properties": {
                                "name": {"type": "string"},
                                "items": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "institution", "degree", "location", "start_date", "end_date",
                            ],
                            "properties": {
                                "institution": {"type": "string"},
                                "degree": {"type": "string"},
                                "location": {"type": "string"},
                                "start_date": {"type": "string"},
                                "end_date": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }
