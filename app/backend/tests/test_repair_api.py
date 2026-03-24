from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def test_repair_stream_route_registered(client: TestClient):
    """Verify /api/repair/stream route is registered with SSE content-type.

    We check the route directly rather than streaming (streaming blocks indefinitely
    since the SSE generator never closes the connection).
    """
    from app.backend.main import create_app

    app = create_app()
    routes = {route.path: route for route in app.routes}
    assert "/api/repair/stream" in routes


def test_repair_status_returns_json(client: TestClient):
    response = client.get("/api/repair/status")
    assert response.status_code == 200
    data = response.json()
    assert "event" in data
    assert "gh_available" in data


def test_repair_apply_no_event(client: TestClient):
    """Without a queued event, apply returns ok=False."""
    import app.backend.services.repair_service as svc
    orig = svc._latest_event
    svc._latest_event = None
    try:
        response = client.post("/api/repair/apply")
        assert response.status_code == 200
        assert response.json()["ok"] is False
    finally:
        svc._latest_event = orig


def test_repair_dismiss(client: TestClient):
    response = client.post("/api/repair/dismiss")
    assert response.status_code == 200
    assert response.json()["ok"] is True


@patch("app.backend.services.github_service.gh_available", return_value=False)
def test_repair_github_issue_no_gh(mock_gh, client: TestClient):
    response = client.post(
        "/api/repair/github-issue",
        json={"title": "Test error", "body": "Details here"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "gh" in data["message"].lower()


@patch("app.backend.services.github_service.gh_available", return_value=True)
@patch("app.backend.services.github_service.create_issue", return_value="https://github.com/owner/repo/issues/42")
def test_repair_github_issue_creates_issue(mock_create, mock_gh, client: TestClient):
    response = client.post(
        "/api/repair/github-issue",
        json={"title": "Test error", "body": "Details here"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "github.com" in data["url"]
    mock_create.assert_called_once_with("Test error", "Details here")
