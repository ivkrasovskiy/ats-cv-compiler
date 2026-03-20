from unittest.mock import MagicMock, patch


def test_doctor_returns_checks_list(client):
    mock_result = MagicMock()
    mock_result.stdout = "✓ uv found\n✗ data/ missing\n"
    mock_result.stderr = ""
    mock_result.returncode = 1

    with patch("app.backend.services.doctor_service.subprocess.run", return_value=mock_result):
        r = client.get("/api/doctor")

    assert r.status_code == 200
    data = r.json()
    assert "checks" in data
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) == 2
    assert "all_ok" in data
    assert data["all_ok"] is False  # ✗ line makes it False


def test_doctor_all_ok_when_all_pass(client):
    mock_result = MagicMock()
    mock_result.stdout = "✓ uv found\n✓ data/ exists\n"
    mock_result.stderr = ""
    mock_result.returncode = 0

    with patch("app.backend.services.doctor_service.subprocess.run", return_value=mock_result):
        r = client.get("/api/doctor")

    data = r.json()
    assert data["all_ok"] is True


def test_lint_returns_ok_when_no_issues(client):
    mock_result = MagicMock()
    mock_result.stdout = "No issues found\n"
    mock_result.stderr = ""
    mock_result.returncode = 0

    with patch("app.backend.api.lint.subprocess.run", return_value=mock_result):
        r = client.get("/api/lint")

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert isinstance(data["issues"], list)


def test_lint_returns_errors_when_issues_found(client):
    mock_result = MagicMock()
    mock_result.stdout = "ERROR: profile.md missing required field 'name'\n"
    mock_result.stderr = ""
    mock_result.returncode = 1

    with patch("app.backend.api.lint.subprocess.run", return_value=mock_result):
        r = client.get("/api/lint")

    data = r.json()
    assert data["ok"] is False
    assert any(i["severity"] == "ERROR" for i in data["issues"])
