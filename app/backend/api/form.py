"""
Structured form API for data file editing.

GET  /api/files/data/{path}/form  → return typed JSON fields
PUT  /api/files/data/{path}/form  → accept JSON fields, serialize to YAML frontmatter, save
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import APIRouter, Body, HTTPException

from app.backend.services.file_service import get_project_root, safe_resolve

router = APIRouter()


def _infer_file_type(path: str) -> str | None:
    """Return file type string or None for unknown paths."""
    p = path.replace("\\", "/")
    if p == "profile.md":
        return "profile"
    if p == "skills.md":
        return "skills"
    if p == "education.md":
        return "education"
    if p.startswith("experience/") and p.endswith(".md"):
        return "experience"
    if p.startswith("projects/") and p.endswith(".md"):
        return "project"
    return None


def _stem_to_id(path: str) -> str:
    """Derive an id from the file stem, stripping llm_/user_ prefixes."""
    stem = Path(path).stem
    stem = re.sub(r"^(?:llm_|user_)", "", stem)
    return re.sub(r"[^a-z0-9_]", "_", stem.lower()).strip("_") or "entry"


def _read_frontmatter_raw(file_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a .md file. Returns empty dict if missing."""
    text = file_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3 or parts[0].strip() != "":
        return {}
    try:
        data = yaml.safe_load(parts[1])
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _build_profile_fields(fm: dict[str, Any]) -> dict[str, Any]:
    links_raw = fm.get("links") or []
    links = []
    if isinstance(links_raw, list):
        for item in links_raw:
            if isinstance(item, dict):
                links.append(
                    {"label": str(item.get("label") or ""), "url": str(item.get("url") or "")}
                )
    return {
        "name": str(fm.get("name") or ""),
        "headline": str(fm.get("headline") or ""),
        "email": str(fm.get("email") or ""),
        "location": str(fm.get("location") or ""),
        "about_me": str(fm.get("about_me") or ""),
        "links": links,
    }


def _build_skills_fields(fm: dict[str, Any]) -> dict[str, Any]:
    cats_raw = fm.get("categories") or []
    categories = []
    if isinstance(cats_raw, list):
        for cat in cats_raw:
            if isinstance(cat, dict):
                items = [str(i) for i in (cat.get("items") or []) if i is not None]
                categories.append({"name": str(cat.get("name") or ""), "items": items})
    return {"categories": categories}


def _build_education_fields(fm: dict[str, Any]) -> dict[str, Any]:
    entries_raw = fm.get("entries") or []
    entries = []
    if isinstance(entries_raw, list):
        for e in entries_raw:
            if isinstance(e, dict):
                entries.append(
                    {
                        "institution": str(e.get("institution") or ""),
                        "degree": str(e.get("degree") or ""),
                        "location": str(e.get("location") or "") if e.get("location") else "",
                        "start_date": str(e.get("start_date") or "") if e.get("start_date") else "",
                        "end_date": str(e.get("end_date") or "") if e.get("end_date") else "",
                    }
                )
    langs_raw = fm.get("languages") or []
    languages = [str(lang) for lang in langs_raw if lang is not None]
    return {"entries": entries, "languages": languages}


def _build_experience_fields(fm: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": str(fm.get("company") or ""),
        "title": str(fm.get("title") or ""),
        "location": str(fm.get("location") or "") if fm.get("location") else "",
        "start_date": str(fm.get("start_date") or "") if fm.get("start_date") else "",
        "end_date": str(fm.get("end_date") or "") if fm.get("end_date") else "",
        "tags": [str(t) for t in (fm.get("tags") or []) if t is not None],
        "keywords": [str(k) for k in (fm.get("keywords") or []) if k is not None],
        "bullets": [str(b) for b in (fm.get("bullets") or []) if b is not None],
    }


def _build_project_fields(fm: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(fm.get("name") or ""),
        "company": str(fm.get("company") or "") if fm.get("company") else "",
        "role": str(fm.get("role") or "") if fm.get("role") else "",
        "start_date": str(fm.get("start_date") or "") if fm.get("start_date") else "",
        "end_date": str(fm.get("end_date") or "") if fm.get("end_date") else "",
        "tags": [str(t) for t in (fm.get("tags") or []) if t is not None],
        "bullets": [str(b) for b in (fm.get("bullets") or []) if b is not None],
    }


def _get_fields(file_type: str, fm: dict[str, Any]) -> dict[str, Any]:
    match file_type:
        case "profile":
            return _build_profile_fields(fm)
        case "skills":
            return _build_skills_fields(fm)
        case "education":
            return _build_education_fields(fm)
        case "experience":
            return _build_experience_fields(fm)
        case "project":
            return _build_project_fields(fm)
        case _:
            return {}


def _validate_profile(fields: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(fields.get("name") or "").strip():
        errors["name"] = "Name is required"
    if not str(fields.get("headline") or "").strip():
        errors["headline"] = "Headline is required"
    if not str(fields.get("location") or "").strip():
        errors["location"] = "Location is required"
    if not str(fields.get("about_me") or "").strip():
        errors["about_me"] = "About me is required"
    return errors


def _validate_skills(fields: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    cats = fields.get("categories") or []
    if not cats:
        errors["categories"] = "At least one skill category is required"
    return errors


def _validate_education(fields: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    entries = fields.get("entries") or []
    if not entries:
        errors["entries"] = "At least one education entry is required"
    return errors


def _validate_experience(fields: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(fields.get("company") or "").strip():
        errors["company"] = "Company is required"
    if not str(fields.get("title") or "").strip():
        errors["title"] = "Title is required"
    if not str(fields.get("start_date") or "").strip():
        errors["start_date"] = "Start date is required"
    return errors


def _validate_project(fields: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not str(fields.get("name") or "").strip():
        errors["name"] = "Project name is required"
    return errors


def _validate_fields(file_type: str, fields: dict[str, Any]) -> dict[str, str]:
    match file_type:
        case "profile":
            return _validate_profile(fields)
        case "skills":
            return _validate_skills(fields)
        case "education":
            return _validate_education(fields)
        case "experience":
            return _validate_experience(fields)
        case "project":
            return _validate_project(fields)
        case _:
            return {}


def _serialize_profile(fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    links = []
    for link in fields.get("links") or []:
        label = str(link.get("label") or "").strip()
        url = str(link.get("url") or "").strip()
        if label or url:
            links.append({"label": label, "url": url})
    data: dict[str, Any] = {
        "id": entry_id,
        "name": str(fields.get("name") or "").strip(),
        "headline": str(fields.get("headline") or "").strip(),
        "location": str(fields.get("location") or "").strip(),
        "about_me": str(fields.get("about_me") or "").strip(),
        "links": links,
    }
    email = str(fields.get("email") or "").strip()
    if email:
        data["email"] = email
    return data


def _serialize_skills(fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    categories = []
    for cat in fields.get("categories") or []:
        name = str(cat.get("name") or "").strip()
        items = [str(i).strip() for i in (cat.get("items") or []) if str(i).strip()]
        if name:
            categories.append({"name": name, "items": items})
    return {"id": entry_id, "categories": categories}


def _serialize_education(fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    entries = []
    for e in fields.get("entries") or []:
        institution = str(e.get("institution") or "").strip()
        degree = str(e.get("degree") or "").strip()
        if institution or degree:
            entry: dict[str, Any] = {"institution": institution, "degree": degree}
            location = str(e.get("location") or "").strip()
            start_date = str(e.get("start_date") or "").strip()
            end_date = str(e.get("end_date") or "").strip()
            if location:
                entry["location"] = location
            if start_date:
                entry["start_date"] = start_date
            if end_date:
                entry["end_date"] = end_date
            entries.append(entry)
    languages = [str(lang).strip() for lang in (fields.get("languages") or []) if str(lang).strip()]
    return {"id": entry_id, "entries": entries, "languages": languages}


def _serialize_experience(fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": entry_id,
        "company": str(fields.get("company") or "").strip(),
        "title": str(fields.get("title") or "").strip(),
        "start_date": str(fields.get("start_date") or "").strip(),
        "tags": [str(t).strip() for t in (fields.get("tags") or []) if str(t).strip()],
        "bullets": [str(b).strip() for b in (fields.get("bullets") or []) if str(b).strip()],
    }
    location = str(fields.get("location") or "").strip()
    end_date = str(fields.get("end_date") or "").strip()
    keywords = [str(k).strip() for k in (fields.get("keywords") or []) if str(k).strip()]
    data["location"] = location or None
    data["end_date"] = end_date or None
    if keywords:
        data["keywords"] = keywords
    return data


def _serialize_project(fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": entry_id,
        "name": str(fields.get("name") or "").strip(),
        "tags": [str(t).strip() for t in (fields.get("tags") or []) if str(t).strip()],
        "bullets": [str(b).strip() for b in (fields.get("bullets") or []) if str(b).strip()],
    }
    company = str(fields.get("company") or "").strip()
    role = str(fields.get("role") or "").strip()
    start_date = str(fields.get("start_date") or "").strip()
    end_date = str(fields.get("end_date") or "").strip()
    data["company"] = company or None
    data["role"] = role or None
    data["start_date"] = start_date or None
    data["end_date"] = end_date or None
    return data


def _serialize_fields(file_type: str, fields: dict[str, Any], entry_id: str) -> dict[str, Any]:
    match file_type:
        case "profile":
            return _serialize_profile(fields, entry_id)
        case "skills":
            return _serialize_skills(fields, entry_id)
        case "education":
            return _serialize_education(fields, entry_id)
        case "experience":
            return _serialize_experience(fields, entry_id)
        case "project":
            return _serialize_project(fields, entry_id)
        case _:
            return {}


def _to_yaml_frontmatter(data: dict[str, Any]) -> str:
    body = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{body}---\n"


@router.get("/files/data/{path:path}/form")
def get_data_file_form(path: str) -> dict:
    file_type = _infer_file_type(path)
    if file_type is None:
        raise HTTPException(400, f"No form available for: {path}")

    root = get_project_root()
    try:
        file_path = safe_resolve(root / "data", path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    fm: dict[str, Any] = {}
    if file_path.exists():
        fm = _read_frontmatter_raw(file_path)

    fields = _get_fields(file_type, fm)
    return {"type": file_type, "fields": fields}


@router.put("/files/data/{path:path}/form")
def put_data_file_form(path: str, body: Annotated[dict, Body()]) -> dict:
    file_type = _infer_file_type(path)
    if file_type is None:
        raise HTTPException(400, f"No form available for: {path}")

    root = get_project_root()
    try:
        file_path = safe_resolve(root / "data", path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    fields = body.get("fields", {})
    if not isinstance(fields, dict):
        raise HTTPException(422, {"_": "fields must be an object"})

    errors = _validate_fields(file_type, fields)
    if errors:
        raise HTTPException(422, errors)

    # Preserve existing id or derive from filename
    existing_id = None
    if file_path.exists():
        fm = _read_frontmatter_raw(file_path)
        existing_id = str(fm.get("id") or "").strip() or None
    entry_id = existing_id or _stem_to_id(path)

    data = _serialize_fields(file_type, fields, entry_id)
    content = _to_yaml_frontmatter(data)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return {"path": path, "saved": True}
