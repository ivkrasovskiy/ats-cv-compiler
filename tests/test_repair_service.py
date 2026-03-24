import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.backend.services.log_service import ErrorEntry
from app.backend.services.repair_service import classify_error, apply_fix


def _make_entry(status=500, traceback="AttributeError: 'NoneType'...", error="crash") -> ErrorEntry:
    return ErrorEntry(
        ts="2026-01-01T00:00:00+00:00",
        method="GET",
        path="/api/build",
        status=status,
        traceback=traceback,
        error=error,
    )


def _mock_cli_output(output: str):
    mock_result = MagicMock()
    mock_result.stdout = output
    mock_result.returncode = 0
    return mock_result


@patch("app.backend.services.repair_service._get_cli_cmd", return_value=["echo"])
@patch("subprocess.run")
def test_classify_logic_error(mock_run, mock_cli):
    classification = {"type": "logic_error", "reason": "Attribute not found", "fix_hint": "Check for None"}
    mock_run.return_value = _mock_cli_output(json.dumps(classification))

    error_type, reason, fix_hint = classify_error(_make_entry())
    assert error_type == "logic_error"
    assert "Attribute" in reason
    assert "None" in fix_hint


@patch("app.backend.services.repair_service._get_cli_cmd", return_value=["echo"])
@patch("subprocess.run")
def test_classify_temporary_error(mock_run, mock_cli):
    classification = {"type": "temporary", "reason": "Connection timeout", "fix_hint": ""}
    mock_run.return_value = _mock_cli_output(json.dumps(classification))

    error_type, reason, _ = classify_error(_make_entry(traceback="TimeoutError..."))
    assert error_type == "temporary"
    assert "timeout" in reason.lower()


@patch("app.backend.services.repair_service._get_cli_cmd", return_value=["echo"])
@patch("subprocess.run")
def test_classify_error_with_json_in_prose(mock_run, mock_cli):
    """CLI output may contain prose around JSON — we extract just the JSON."""
    output = 'Here is my analysis: {"type": "logic_error", "reason": "Bad import", "fix_hint": "Fix the import"} — hope that helps!'
    mock_run.return_value = _mock_cli_output(output)

    error_type, reason, fix_hint = classify_error(_make_entry())
    assert error_type == "logic_error"


@patch("app.backend.services.repair_service._get_cli_cmd", return_value=["echo"])
@patch("subprocess.run")
def test_apply_fix_calls_git_stash(mock_run, mock_cli, tmp_path: Path):
    mock_run.return_value = MagicMock(returncode=0, stdout="Fixed", stderr="")

    apply_fix(_make_entry(), "Check for None", tmp_path)

    calls = mock_run.call_args_list
    # First call should be git stash
    first_call_args = calls[0][0][0]
    assert first_call_args[:2] == ["git", "stash"]


@patch("app.backend.services.repair_service._get_cli_cmd", return_value=["echo"])
@patch("subprocess.run")
def test_apply_fix_returns_output(mock_run, mock_cli, tmp_path: Path):
    mock_run.return_value = MagicMock(returncode=0, stdout="Applied fix successfully", stderr="")

    output = apply_fix(_make_entry(), "Fix it", tmp_path)
    # The second subprocess.run is the CLI fix; its stdout is returned
    assert isinstance(output, str)
