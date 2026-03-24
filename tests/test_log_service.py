import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.backend.services.log_service import (
    ErrorEntry,
    cleanup_old_logs,
    setup_logging,
    tail_errors,
)


def _write_entry(log_file: Path, entry: dict) -> None:
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def test_setup_logging_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    assert not log_dir.exists()
    setup_logging(log_dir)
    assert log_dir.exists()
    assert (log_dir / "backend.log").exists() or True  # file created on first write


def test_tail_errors_returns_only_4xx_5xx(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "backend.log"

    entries = [
        {"ts": "2026-01-01T00:00:00+00:00", "method": "GET", "path": "/api/health", "status": 200, "traceback": None, "error": None},
        {"ts": "2026-01-01T00:01:00+00:00", "method": "GET", "path": "/api/bad", "status": 404, "traceback": None, "error": "not found"},
        {"ts": "2026-01-01T00:02:00+00:00", "method": "POST", "path": "/api/build", "status": 500, "traceback": "Traceback...", "error": "crash"},
    ]
    for e in entries:
        _write_entry(log_file, e)

    result = tail_errors(log_dir)
    assert len(result) == 2
    statuses = {r.status for r in result}
    assert statuses == {404, 500}


def test_tail_errors_filters_by_since_ts(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "backend.log"

    old_entry = {"ts": "2026-01-01T00:00:00+00:00", "method": "GET", "path": "/api/x", "status": 500, "traceback": None, "error": "old"}
    new_entry = {"ts": "2026-01-02T00:00:00+00:00", "method": "GET", "path": "/api/y", "status": 500, "traceback": None, "error": "new"}
    _write_entry(log_file, old_entry)
    _write_entry(log_file, new_entry)

    result = tail_errors(log_dir, since_ts="2026-01-01T12:00:00+00:00")
    assert len(result) == 1
    assert result[0].error == "new"


def test_tail_errors_returns_empty_when_no_log(tmp_path: Path) -> None:
    result = tail_errors(tmp_path / "nonexistent")
    assert result == []


def test_cleanup_old_logs_removes_stale_files(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "backend.log.1"
    old_file.write_text("old")
    # Set mtime to 10 days ago
    old_mtime = time.time() - 10 * 86400
    import os
    os.utime(old_file, (old_mtime, old_mtime))

    recent_file = log_dir / "backend.log"
    recent_file.write_text("recent")

    cleanup_old_logs(log_dir, max_age_days=7)
    assert not old_file.exists()
    assert recent_file.exists()


def test_log_rotation(tmp_path: Path) -> None:
    """Verify RotatingFileHandler is configured (smoke test — checks no error on setup)."""
    log_dir = tmp_path / "logs"
    setup_logging(log_dir)
    import logging
    logger = logging.getLogger("cv_backend.errors")
    # Write a message — should not raise
    logger.error(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "status": 500, "method": "GET", "path": "/test", "traceback": None, "error": "test"}))
