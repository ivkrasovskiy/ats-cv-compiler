import subprocess
import threading
import uuid

from app.backend.services.file_service import get_project_root

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def start_build(job_path: str | None, llm: str) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "running", "lines": [], "exit_code": None}

    thread = threading.Thread(target=_run_build, args=(job_id, job_path, llm), daemon=True)
    thread.start()
    return job_id


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None


def get_job_lines(job_id: str) -> list[str]:
    with _lock:
        job = _jobs.get(job_id)
        return list(job["lines"]) if job is not None else []


def _run_build(job_id: str, job_path: str | None, llm: str) -> None:
    root = get_project_root()
    cmd = ["uv", "run", "cv", "build", "--job", job_path or "false"]
    if llm and llm != "none":
        cmd += ["--llm", llm]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=root,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            with _lock:
                _jobs[job_id]["lines"].append(line.rstrip("\n"))
        proc.wait()
        with _lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["exit_code"] = proc.returncode
    except Exception as exc:
        with _lock:
            _jobs[job_id]["lines"].append(f"ERROR: {exc}")
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["exit_code"] = 1
