from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def test_agent_ws_unknown_cli_rejected(client: TestClient):
    """Unknown CLI should close the connection with code 4000 before accepting."""
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/agent?cli=unknown_cli_xyz"):
            pass

    assert exc_info.value.code == 4000


@patch("app.backend.api.agent.start_session")
@patch("app.backend.api.agent.pty_reader")
@patch("app.backend.api.agent.ws_reader")
def test_agent_ws_starts_session(mock_ws_reader, mock_pty_reader, mock_start, client: TestClient):
    """WebSocket accepts connection and starts a PTY session for known CLI."""

    async def _noop(*_args, **_kwargs):
        return

    mock_pty_reader.side_effect = _noop
    mock_ws_reader.side_effect = _noop

    mock_session = MagicMock()
    mock_session.master_fd = -1
    mock_session.proc = MagicMock()
    mock_session.proc.pid = None
    mock_start.return_value = mock_session

    with client.websocket_connect("/ws/agent?cli=claude") as ws:
        pass  # Disconnect immediately

    # start_session was called → connection was accepted
    mock_start.assert_called_once()
    call_kwargs = mock_start.call_args
    assert call_kwargs[0][0] == "claude" or call_kwargs[1].get("cli") == "claude"
