import os
from pathlib import Path


def get_project_root() -> Path:
    return Path(os.environ.get("CV_PROJECT_ROOT", str(Path.cwd()))).resolve()


def safe_resolve(base: Path, relative: str) -> Path:
    """Resolve path relative to base, raising ValueError if it escapes."""
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"Path traversal detected: {relative!r}") from exc
    return resolved


def read_file(base: Path, relative: str) -> str:
    path = safe_resolve(base, relative)
    return path.read_text(encoding="utf-8")


def write_file(base: Path, relative: str, content: str) -> None:
    path = safe_resolve(base, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def delete_file(base: Path, relative: str) -> None:
    path = safe_resolve(base, relative)
    path.unlink()


def file_tree(base: Path) -> list[dict]:
    """Recursive sorted list of files under base."""
    if not base.exists():
        return []
    result = []
    for p in sorted(base.rglob("*")):
        if p.is_file() and not any(part.startswith(".") for part in p.parts[len(base.parts) :]):
            st = p.stat()
            result.append({
                "path": str(p.relative_to(base)),
                "name": p.name,
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
    return result
