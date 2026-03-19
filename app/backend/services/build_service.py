import os
import subprocess
import threading
import uuid
from pathlib import Path

from app.backend.services.file_service import get_project_root

_jobs: dict[str, dict] = {}
_lock = threading.Lock()

_LLM_FAIL_MARKERS = frozenset(
    [
        "LLM_GENERATION_FAILED",
        "LLM_SKILL_HIGHLIGHT_FAILED",
        "LLM_SKILL_SELECT_FAILED",
        "LLM_SUMMARY_FAILED",
    ]
)


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


def start_build_from_md(md_path: str) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "running", "lines": [], "exit_code": None}

    thread = threading.Thread(target=_run_build_from_md, args=(job_id, md_path), daemon=True)
    thread.start()
    return job_id


def _append_line(job_id: str, line: str) -> None:
    with _lock:
        _jobs[job_id]["lines"].append(line)


def _finish(job_id: str, exit_code: int) -> None:
    with _lock:
        _jobs[job_id]["status"] = "done" if exit_code == 0 else "error"
        _jobs[job_id]["exit_code"] = exit_code


def _run_subprocess_streaming(
    job_id: str,
    root: Path,
    cmd: list[str],
    env: dict[str, str] | None = None,
) -> tuple[list[str], int]:
    """Run cmd, stream each line to the job log, and return (all_lines, exit_code)."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=root,
            env=env,
        )
        assert proc.stdout is not None
        collected: list[str] = []
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            collected.append(line)
            _append_line(job_id, line)
        proc.wait()
        return collected, proc.returncode or 0
    except Exception as exc:
        _append_line(job_id, f"ERROR: {exc}")
        return [], 1


def _provider_chain(root: Path) -> list[tuple[str, str | None]]:
    """Return [(display_name, CV_CODEX_CMD_override)] in fallback order.

    The last entry is always (no-AI, None) — the deterministic fallback.
    A None codex_cmd means "use whatever is already set in the environment".
    """
    try:
        from cv_compiler.llm.config import read_env_file

        env_path = root / "config" / "llm.env"
        file_values = read_env_file(env_path) if env_path.exists() else {}
    except Exception:
        file_values = {}

    provider = (
        (os.getenv("CV_AI_PROVIDER") or file_values.get("CV_AI_PROVIDER") or "gemini")
        .strip()
        .lower()
    )

    chain: list[tuple[str, str | None]] = []
    if provider == "claude":
        chain.append(("Claude", "claude"))
        chain.append(("Gemini", "gemini"))
    elif provider == "gemini":
        chain.append(("Gemini", "gemini"))
    else:
        # custom / unknown — use whatever CV_CODEX_CMD is already configured
        chain.append(("Custom AI", None))

    chain.append(("deterministic pipeline", None))
    return chain


def _run_build_from_md(job_id: str, md_path: str) -> None:
    root = get_project_root()
    cmd = ["uv", "run", "cv", "build", "--from-markdown", md_path]
    _, exit_code = _run_subprocess_streaming(job_id, root, cmd)
    _finish(job_id, exit_code)


def _run_build(job_id: str, job_path: str | None, llm: str) -> None:
    if llm == "auto":
        _run_build_auto(job_id, job_path)
        return

    root = get_project_root()
    cmd = ["uv", "run", "cv", "build", "--job", job_path or "false"]
    if llm and llm != "none":
        cmd += ["--llm", llm]
    _, exit_code = _run_subprocess_streaming(job_id, root, cmd)
    _finish(job_id, exit_code)


def _run_build_auto(job_id: str, job_path: str | None) -> None:
    """Try each AI provider in order, falling back gracefully to the deterministic pipeline."""
    root = get_project_root()
    chain = _provider_chain(root)
    ai_providers = chain[:-1]  # all except the no-AI fallback
    total_steps = len(chain)   # AI providers + 1 deterministic fallback

    for step, (display_name, codex_cmd) in enumerate(ai_providers, start=1):
        # [STEP M/N] lines are parsed by the frontend as progress markers (not shown in log)
        _append_line(job_id, f"[STEP {step}/{total_steps}] {display_name}")
        env = dict(os.environ)
        if codex_cmd:
            env["CV_CODEX_CMD"] = codex_cmd
            env["CV_CODEX_ARGS"] = "-p"
        cmd = ["uv", "run", "cv", "build", "--job", job_path or "false", "--llm", "agents"]
        lines, exit_code = _run_subprocess_streaming(job_id, root, cmd, env)

        if exit_code != 0:
            _append_line(job_id, f"[⚠] {display_name} failed (exit {exit_code})")
            continue

        failed = [ln for ln in lines if any(m in ln for m in _LLM_FAIL_MARKERS)]
        if failed:
            reason = failed[-1].split(":", 2)[-1].strip()
            _append_line(job_id, f"[⚠] {display_name}: {reason}")
            continue

        # AI succeeded
        _finish(job_id, 0)
        return

    # All AI providers failed — deterministic fallback
    _append_line(job_id, f"[STEP {total_steps}/{total_steps}] Deterministic pipeline")
    _append_line(job_id, "[→] All AI providers unavailable — using your original bullets.")
    cmd = ["uv", "run", "cv", "build", "--job", job_path or "false"]
    _, exit_code = _run_subprocess_streaming(job_id, root, cmd)
    _finish(job_id, exit_code)
