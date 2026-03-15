from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse

from app.backend.services.file_service import (
    delete_file,
    file_tree,
    get_project_root,
    read_file,
    safe_resolve,
    write_file,
)

router = APIRouter()


# ── data/ ────────────────────────────────────────────────────────────────────

@router.get("/files/data")
def list_data_files() -> list[dict]:
    return file_tree(get_project_root() / "data")


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


@router.get("/files/jobs/{name}")
def get_job_file(name: str) -> dict:
    root = get_project_root()
    try:
        content = read_file(root / "jobs", name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Job file not found: {name}") from exc
    return {"name": name, "content": content}


@router.put("/files/jobs/{name}")
def put_job_file(name: str, body: Annotated[dict, Body()]) -> dict:
    root = get_project_root()
    try:
        write_file(root / "jobs", name, body.get("content", ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"name": name, "saved": True}


@router.delete("/files/jobs/{name}")
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
