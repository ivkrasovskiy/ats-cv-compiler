import json
import logging
import logging.handlers
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ErrorEntry:
    ts: str
    method: str
    path: str
    status: int
    traceback: str | None
    error: str | None


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"

    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    backend_logger = logging.getLogger("cv_backend.errors")
    backend_logger.setLevel(logging.ERROR)
    backend_logger.addHandler(handler)
    backend_logger.propagate = False

    # Frontend errors logger
    frontend_log_file = log_dir / "frontend.log"
    fe_handler = logging.handlers.RotatingFileHandler(
        frontend_log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fe_handler.setFormatter(logging.Formatter("%(message)s"))
    frontend_logger = logging.getLogger("cv_backend.frontend_errors")
    frontend_logger.setLevel(logging.ERROR)
    frontend_logger.addHandler(fe_handler)
    frontend_logger.propagate = False


def cleanup_old_logs(log_dir: Path, max_age_days: int = 7) -> None:
    if not log_dir.exists():
        return
    cutoff = time.time() - max_age_days * 86400
    for f in log_dir.glob("*.log*"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)


def tail_errors(log_dir: Path, since_ts: str | None = None) -> list[ErrorEntry]:
    log_file = log_dir / "backend.log"
    if not log_file.exists():
        return []

    since_dt: datetime | None = None
    if since_ts:
        try:
            since_dt = datetime.fromisoformat(since_ts)
        except ValueError:
            pass

    entries: list[ErrorEntry] = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            status = data.get("status", 0)
            if status < 400:
                continue

            if since_dt:
                try:
                    entry_dt = datetime.fromisoformat(data["ts"])
                    if entry_dt <= since_dt:
                        continue
                except (KeyError, ValueError):
                    pass

            entries.append(
                ErrorEntry(
                    ts=data.get("ts", ""),
                    method=data.get("method", ""),
                    path=data.get("path", ""),
                    status=status,
                    traceback=data.get("traceback"),
                    error=data.get("error"),
                )
            )

    return entries
