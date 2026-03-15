import subprocess

from fastapi import APIRouter

from app.backend.services.file_service import get_project_root

router = APIRouter()


@router.get("/lint")
def get_lint() -> dict:
    root = get_project_root()
    proc = subprocess.run(
        ["uv", "run", "cv", "lint"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    issues = []
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if "ERROR" in upper:
            severity = "ERROR"
        elif "WARNING" in upper or "WARN" in upper:
            severity = "WARNING"
        else:
            severity = "INFO"
        issues.append({"message": line, "severity": severity})
    return {"issues": issues, "exit_code": proc.returncode, "ok": proc.returncode == 0}
