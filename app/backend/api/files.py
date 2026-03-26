import logging
import shutil
from pathlib import Path
from typing import Annotated

import yaml
from fastapi import APIRouter, Body, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.backend.services.file_service import (
    delete_file,
    file_tree,
    get_project_root,
    read_file,
    safe_resolve,
    write_file,
)
from cv_compiler.parse.frontmatter import parse_markdown_frontmatter

logger = logging.getLogger(__name__)
router = APIRouter()


# ── data/ ────────────────────────────────────────────────────────────────────


def _read_company(file_path: Path) -> str | None:
    """Read company field from YAML frontmatter."""
    try:
        doc = parse_markdown_frontmatter(file_path)
        return str(doc.frontmatter.get("company") or "").strip() or None
    except Exception:
        return None


@router.get("/files/data")
def list_data_files() -> list[dict]:
    root = get_project_root()
    files = file_tree(root / "data")
    for f in files:
        path = f["path"]
        if path.startswith(("experience/", "projects/")) and path.endswith(".md"):
            try:
                file_path = safe_resolve(root / "data", path)
                company = _read_company(file_path)
                if company:
                    f["company"] = company
            except Exception:
                pass
    return files


@router.get("/files/data/{path:path}")
def get_data_file(path: str) -> dict:
    root = get_project_root()
    try:
        content = read_file(root / "data", path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"File not found: {path}") from exc
    return {"path": path, "content": content}


@router.put("/files/data/{path:path}")
def put_data_file(path: str, body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    try:
        write_file(root / "data", path, body.get("content", ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"path": path, "saved": True}


# ── jobs/ ────────────────────────────────────────────────────────────────────


@router.get("/files/jobs")
def list_job_files() -> list[dict]:
    return file_tree(get_project_root() / "jobs")


@router.get("/files/jobs/{name:path}")
def get_job_file(name: str) -> dict:
    root = get_project_root()
    try:
        content = read_file(root / "jobs", name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Job file not found: {name}") from exc
    return {"name": name, "content": content}


@router.put("/files/jobs/{name:path}")
def put_job_file(name: str, body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    try:
        write_file(root / "jobs", name, body.get("content", ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"name": name, "saved": True}


@router.delete("/files/jobs/{name:path}")
def delete_job_file(name: str) -> dict:
    root = get_project_root()
    try:
        delete_file(root / "jobs", name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Job file not found: {name}") from exc
    return {"name": name, "deleted": True}


# ── out/ ─────────────────────────────────────────────────────────────────────


@router.get("/out")
def list_out_files() -> list[dict]:
    return file_tree(get_project_root() / "out")


@router.get("/out/{filename}")
def get_out_file(filename: str) -> FileResponse:
    root = get_project_root()
    try:
        path = safe_resolve(root / "out", filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not path.exists():
        raise HTTPException(404, f"Output file not found: {filename}")
    return FileResponse(path)


@router.put("/out/{filename}")
def put_out_file(filename: str, body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    try:
        write_file(root / "out", filename, body.get("content", ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"filename": filename, "saved": True}


# ── delete data files ────────────────────────────────────────────────────────


@router.delete("/files/data/{path:path}")
def delete_data_file(path: str) -> dict:
    # Only allow experience/ and projects/ prefixes
    if not (path.startswith("experience/") or path.startswith("projects/")):
        raise HTTPException(400, f"Deletion not allowed for: {path}")
    root = get_project_root()
    try:
        delete_file(root / "data", path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"File not found: {path}") from exc
    return {"path": path, "deleted": True}


# ── delete / rename out files ─────────────────────────────────────────────────


@router.delete("/out/{filename}")
def delete_out_file(filename: str) -> dict:
    root = get_project_root()
    try:
        delete_file(root / "out", filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Output file not found: {filename}") from exc
    return {"filename": filename, "deleted": True}


@router.post("/out/rename")
def rename_out_file(body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    from_name = body.get("from", "")
    to_name = body.get("to", "")
    if not from_name or not to_name:
        raise HTTPException(400, "Both 'from' and 'to' are required")
    try:
        from_path = safe_resolve(root / "out", from_name)
        to_path = safe_resolve(root / "out", to_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not from_path.exists():
        raise HTTPException(404, f"File not found: {from_name}")
    from_path.rename(to_path)
    return {"from": from_name, "to": to_name, "renamed": True}


# ── prompts/ ─────────────────────────────────────────────────────────────────


@router.get("/files/prompts")
def list_prompt_files() -> list[dict]:
    return file_tree(get_project_root() / "prompts")


@router.get("/files/prompts/{path:path}")
def get_prompt_file(path: str) -> dict:
    root = get_project_root()
    try:
        content = read_file(root / "prompts", path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Prompt file not found: {path}") from exc
    return {"path": path, "content": content}


@router.put("/files/prompts/{path:path}")
def put_prompt_file(path: str, body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    content = body.get("content", "")
    # Validate YAML files before writing
    if path.endswith((".yaml", ".yml")):
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise HTTPException(422, f"Invalid YAML: {exc}") from exc
    try:
        write_file(root / "prompts", path, content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"path": path, "saved": True}


# ── upload cv pdf ─────────────────────────────────────────────────────────────


@router.post("/upload/cv-pdf")
async def upload_cv_pdf(file: UploadFile) -> dict:
    root = get_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    dest = data_dir / "cv.pdf"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"saved": True, "path": "data/cv.pdf"}


# ── ingest pdf ────────────────────────────────────────────────────────────────


@router.post("/ingest/pdf")
def run_ingest_pdf() -> dict:
    from cv_compiler.ingest.pdf_ingest import ingest_pdf_to_markdown
    from cv_compiler.llm.provider import resolve_from_env

    root = get_project_root()
    pdf_path = root / "data" / "cv.pdf"
    if not pdf_path.exists():
        raise HTTPException(400, "data/cv.pdf not found. Upload a PDF first.")

    try:
        resolved = resolve_from_env(root / "config" / "llm.env")
        result = ingest_pdf_to_markdown(
            data_dir=root / "data",
            pdf_path=pdf_path,
            llm_mode=resolved.ingest_mode,
            llm_config=resolved.llm_config,
            codex_config=resolved.codex_config,
            prompt_path=root / "prompts" / "pdf_ingest_prompt.md",
            overwrite=True,
        )
    except Exception as exc:
        logger.exception("PDF ingest failed")
        raise HTTPException(500, str(exc)) from exc

    return {
        "written": [str(p.relative_to(root)) for p in result.written_paths],
        "warnings": list(result.warnings),
    }
