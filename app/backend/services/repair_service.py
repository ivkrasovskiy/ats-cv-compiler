"""Background service that watches backend.log for errors and optionally auto-repairs them."""

from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.backend.services.log_service import ErrorEntry, tail_errors


@dataclass
class RepairEvent:
    id: str
    ts: str
    error_entry: dict
    error_type: str  # "temporary" | "logic_error" | "unknown"
    reason: str
    fix_hint: str
    status: str = "pending"  # "pending" | "fixing" | "fix_applied" | "dismissed" | "failed"
    fix_output: str = ""
    gh_issue_url: str = ""


_subscribers: list[asyncio.Queue[dict]] = []
_latest_event: RepairEvent | None = None
_last_check_ts: str | None = None

POLL_INTERVAL = 60  # seconds


def subscribe() -> asyncio.Queue[dict]:
    """Register a new SSE connection; returns a queue that receives live events."""
    q: asyncio.Queue[dict] = asyncio.Queue()
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue[dict]) -> None:
    """Remove a disconnected SSE client's queue."""
    try:
        _subscribers.remove(q)
    except ValueError:
        pass


async def _broadcast(event: dict) -> None:
    for q in list(_subscribers):
        await q.put(event)


def get_latest_event() -> RepairEvent | None:
    return _latest_event


def _get_repair_mode() -> str:
    from app.backend.services.file_service import get_project_root
    from cv_compiler.llm.config import read_env_file

    env_path = get_project_root() / "config" / "llm.env"
    values = read_env_file(env_path)
    return values.get("CV_REPAIR_MODE", "silent")


def _get_cli_cmd() -> list[str]:
    from app.backend.services.file_service import get_project_root
    from cv_compiler.llm.config import read_env_file

    env_path = get_project_root() / "config" / "llm.env"
    values = read_env_file(env_path)
    provider = values.get("CV_AI_PROVIDER", "claude")
    if provider == "claude":
        return ["claude"]
    elif provider == "gemini":
        return ["gemini"]
    return ["claude"]


def classify_error(entry: ErrorEntry) -> tuple[str, str, str]:
    """Return (error_type, reason, fix_hint) by asking the CLI."""
    prompt = (
        "Classify this backend error. Reply with ONLY a JSON object (no markdown, no explanation): "
        '{"type":"temporary"|"logic_error","reason":"...","fix_hint":"..."}. '
        f"Error details: status={entry.status}, path={entry.path}, "
        f"error={entry.error!r}, traceback={entry.traceback!r}"
    )
    cli = _get_cli_cmd()
    try:
        result = subprocess.run(
            cli + ["-p", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        # Extract JSON from output
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(output[start:end])
            return (
                data.get("type", "unknown"),
                data.get("reason", ""),
                data.get("fix_hint", ""),
            )
    except Exception:
        pass
    return ("unknown", "Could not classify", "")


def apply_fix(entry: ErrorEntry, fix_hint: str, project_root: Path) -> str:
    """Run git stash + CLI fix. Returns fix output."""
    # Safety net
    subprocess.run(
        ["git", "stash", "--include-untracked", "-m", "auto-repair-snapshot"],
        cwd=str(project_root),
        capture_output=True,
    )

    prompt = (
        "Fix this backend error in the codebase. "
        f"Traceback: {entry.traceback!r}. "
        f"Hint: {fix_hint}. "
        "Edit the relevant Python source files to fix the root cause. "
        "Do not explain; just fix."
    )
    cli = _get_cli_cmd()
    try:
        result = subprocess.run(
            cli + ["-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root),
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as exc:
        return str(exc)


async def repair_loop(log_dir: Path, project_root: Path) -> None:
    global _latest_event, _last_check_ts

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            entries = tail_errors(log_dir, since_ts=_last_check_ts)
            if entries:
                _last_check_ts = datetime.now(UTC).isoformat()

            for entry in entries:
                error_type, reason, fix_hint = classify_error(entry)
                event = RepairEvent(
                    id=f"repair-{datetime.now(UTC).timestamp()}",
                    ts=datetime.now(UTC).isoformat(),
                    error_entry={
                        "ts": entry.ts,
                        "method": entry.method,
                        "path": entry.path,
                        "status": entry.status,
                        "traceback": entry.traceback,
                        "error": entry.error,
                    },
                    error_type=error_type,
                    reason=reason,
                    fix_hint=fix_hint,
                )
                _latest_event = event
                await _broadcast({"type": "logic_error", "event": _event_to_dict(event)})

                mode = _get_repair_mode()
                if mode == "silent" and error_type == "logic_error":
                    event.status = "fixing"
                    await _broadcast({"type": "fixing", "event": _event_to_dict(event)})
                    output = await asyncio.get_event_loop().run_in_executor(
                        None, apply_fix, entry, fix_hint, project_root
                    )
                    event.fix_output = output
                    event.status = "fix_applied"
                    await _broadcast({"type": "fix_applied", "event": _event_to_dict(event)})
        except Exception:
            pass


def _event_to_dict(event: RepairEvent) -> dict:
    return {
        "id": event.id,
        "ts": event.ts,
        "error_entry": event.error_entry,
        "error_type": event.error_type,
        "reason": event.reason,
        "fix_hint": event.fix_hint,
        "status": event.status,
        "fix_output": event.fix_output,
        "gh_issue_url": event.gh_issue_url,
    }
