"""Write parsed CV data to canonical Markdown files and manage backups."""

from __future__ import annotations

import hashlib
import re
import shutil
import time
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from .pdf_models import IngestResult, ParsedCv, ParsedProject

_SAFE_ID_RE = re.compile(r"[^a-z0-9_]+")
_MAX_SLUG_LEN = 50

# Cyrillic → Latin transliteration table (covers full Russian alphabet)
_CYRILLIC: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "j",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}
_PLACEHOLDER = "TODO: edit this field"


def write_ingest_files(data_dir: Path, parsed: ParsedCv, *, overwrite: bool) -> IngestResult:
    warnings: list[str] = []
    written: list[Path] = []
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = _backup_ingest_files(data_dir, overwrite=overwrite)

    try:
        used_ids: set[str] = {"profile", "skills", "education"}

        profile_path = data_dir / "profile.md"
        _ensure_writable(profile_path, overwrite=False)
        profile_frontmatter = {
            "id": "profile",
            "name": _require_field(parsed.profile.name, "profile.name", warnings),
            "headline": _require_field(parsed.profile.headline, "profile.headline", warnings),
            "location": _require_field(parsed.profile.location, "profile.location", warnings),
            "email": parsed.profile.email,
            "links": [
                {
                    "label": _require_field(link.label, "profile.links.label", warnings),
                    "url": link.url or "",
                }
                for link in parsed.profile.links
                if link.label or link.url
            ],
            "about_me": _require_field(parsed.profile.about_me, "profile.about_me", warnings),
        }
        _write_frontmatter(profile_path, profile_frontmatter, note="Generated from PDF.")
        written.append(profile_path)

        skills_path = data_dir / "skills.md"
        _ensure_writable(skills_path, overwrite=False)
        skills_frontmatter = {
            "id": "skills",
            "categories": [
                {
                    "name": _require_field(cat.name, "skills.category.name", warnings),
                    "items": list(cat.items),
                }
                for cat in parsed.skills
            ],
        }
        _write_frontmatter(skills_path, skills_frontmatter, note="Generated from PDF.")
        written.append(skills_path)

        education_path = data_dir / "education.md"
        _ensure_writable(education_path, overwrite=False)
        education_frontmatter = {
            "id": "education",
            "entries": [
                {
                    "institution": _require_field(e.institution, "education.institution", warnings),
                    "degree": _require_field(e.degree, "education.degree", warnings),
                    "location": e.location,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                }
                for e in parsed.education
            ],
        }
        _write_frontmatter(education_path, education_frontmatter, note="Generated from PDF.")
        written.append(education_path)

        # Derive projects from experience entries
        derived_projects: list[ParsedProject] = []
        for idx, entry in enumerate(parsed.experience, start=1):
            name_parts = [entry.company or "", entry.title or ""]
            name = " - ".join(part for part in name_parts if part.strip())
            if not name:
                name = f"Project {idx}"
            derived_projects.append(
                ParsedProject(
                    name=name,
                    company=entry.company,
                    role=entry.title,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    bullets=entry.bullets,
                    tags=entry.tags,
                )
            )

        projects_dir = data_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        for idx, entry in enumerate(list(parsed.projects) + derived_projects, start=1):
            proj_id = _unique_id(_slugify(f"proj_{entry.name or idx}"), used_ids)
            used_ids.add(proj_id)
            proj_path = projects_dir / f"{proj_id}.md"
            _ensure_writable(proj_path, overwrite=False)
            proj_frontmatter = {
                "id": proj_id,
                "name": _require_field(entry.name, "projects.name", warnings),
                "company": entry.company,
                "role": entry.role,
                "start_date": entry.start_date,
                "end_date": entry.end_date,
                "tags": list(entry.tags),
                "bullets": list(entry.bullets),
            }
            _write_frontmatter(proj_path, proj_frontmatter, note="Generated from PDF.")
            written.append(proj_path)
    except Exception:
        if backup_dir is not None:
            _remove_written_files(written)
            _restore_ingest_backup(backup_dir, data_dir)
        raise

    if backup_dir is not None:
        shutil.rmtree(backup_dir, ignore_errors=True)

    return IngestResult(written_paths=tuple(written), warnings=tuple(warnings))


def _write_frontmatter(path: Path, frontmatter: dict[str, Any], note: str) -> None:
    content = "---\n"
    content += yaml.safe_dump(frontmatter, sort_keys=False).strip()
    content += "\n---\n\n"
    content += "Notes (not rendered):\n"
    content += f"- {note}\n"
    path.write_text(content, encoding="utf-8")


def _collect_ingest_files(data_dir: Path) -> tuple[Path, ...]:
    candidates = [data_dir / "profile.md", data_dir / "skills.md", data_dir / "education.md"]
    for subdir in ("projects", "experience"):
        dir_path = data_dir / subdir
        if dir_path.exists():
            candidates.extend(sorted(dir_path.glob("*.md")))
    return tuple(path for path in candidates if path.exists())


def _backup_ingest_files(data_dir: Path, *, overwrite: bool) -> Path | None:
    if not overwrite:
        return None
    candidates = _collect_ingest_files(data_dir)
    if not candidates:
        return None
    backup_root = data_dir.parent / "tmp"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_root / f"ingest_backup_{int(time.time() * 1000)}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in candidates:
        rel = path.relative_to(data_dir)
        dest = backup_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, dest)
    return backup_dir


def _restore_ingest_backup(backup_dir: Path, data_dir: Path) -> None:
    if not backup_dir.exists():
        return
    for path in sorted(backup_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(backup_dir)
        dest = data_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        shutil.move(path, dest)
    shutil.rmtree(backup_dir, ignore_errors=True)


def _remove_written_files(written: list[Path]) -> None:
    for path in written:
        if path.exists():
            path.unlink()


def _ensure_writable(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(f"Refusing to overwrite existing file: {path}")


def _slugify(text: str) -> str:
    text = text.strip().lower()
    # Transliterate Cyrillic, then NFKD-normalize accented Latin
    chars = [_CYRILLIC.get(ch, ch) for ch in text]
    ascii_text = unicodedata.normalize("NFKD", "".join(chars))
    ascii_text = ascii_text.encode("ascii", errors="ignore").decode("ascii")
    slug = _SAFE_ID_RE.sub("_", ascii_text).strip("_")
    slug = slug[:_MAX_SLUG_LEN].rstrip("_")
    # Non-Latin fallback (Chinese, Arabic, etc.): stable short hash
    return slug or "item_" + hashlib.sha1(text.encode()).hexdigest()[:8]


def _unique_id(base: str, used: set[str]) -> str:
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def _require_field(value: str | None, field: str, warnings: list[str]) -> str:
    if value:
        return value
    warnings.append(f"Missing {field}; set placeholder.")
    return _PLACEHOLDER
