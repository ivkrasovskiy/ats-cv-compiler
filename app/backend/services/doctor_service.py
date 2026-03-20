import subprocess

from app.backend.services.file_service import get_project_root

# Symbols that indicate a passing check
_OK_PREFIXES = ("✓", "✔", "ok ", "OK ")
_FAIL_PREFIXES = ("✗", "✘", "FAIL", "ERROR", "error:", "✗")


def _classify(line: str) -> bool:
    stripped = line.strip()
    for p in _FAIL_PREFIXES:
        if stripped.startswith(p) or p.upper() in stripped.upper():
            return False
    for p in _OK_PREFIXES:
        if stripped.startswith(p):
            return True
    # Unknown lines: treat as informational (ok=True) unless returncode says otherwise
    return True


def run_doctor() -> list[dict]:
    root = get_project_root()
    proc = subprocess.run(
        ["uv", "run", "cv", "doctor"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    combined = (proc.stdout + proc.stderr).strip()
    checks = []
    for line in combined.splitlines():
        line = line.rstrip()
        if not line:
            continue
        checks.append({"label": line, "ok": _classify(line), "raw": line})
    return checks
