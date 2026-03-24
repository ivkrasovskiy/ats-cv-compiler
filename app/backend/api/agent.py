import asyncio
from pathlib import Path

from fastapi import APIRouter, WebSocket

from app.backend.services.agent_service import pty_reader, start_session, ws_reader
from app.backend.services.file_service import get_project_root

router = APIRouter()


def _check_credentials(provider: str) -> bool:
    """Return True if the CLI for this provider appears to be authenticated.

    Uses only file existence checks — no subprocess, no keychain access,
    no permission dialogs.
    """
    if provider == "gemini":
        # oauth_creds.json is written by Gemini CLI on first login
        cred = Path.home() / ".gemini" / "oauth_creds.json"
        return cred.exists() and cred.stat().st_size > 10
    if provider == "claude":
        # history.jsonl is written on first successful CLI interaction;
        # you cannot interact with Claude Code without logging in first
        history = Path.home() / ".claude" / "history.jsonl"
        return history.exists() and history.stat().st_size > 0
    return True  # unknown provider — don't warn


@router.get("/api/agent/auth-status")
def agent_auth_status():
    from app.backend.services.config_service import read_config
    config = read_config()
    provider = config.get("basic", {}).get("CV_AI_PROVIDER", "gemini")
    return {"provider": provider, "logged_in": _check_credentials(provider)}


@router.websocket("/ws/agent")
async def agent_ws(ws: WebSocket, cli: str = "claude"):
    from app.backend.services.agent_service import _resolve_cli

    # Validate CLI before accepting
    try:
        _resolve_cli(cli)
    except ValueError as exc:
        await ws.close(code=4000, reason=str(exc))
        return

    await ws.accept()
    project_root = get_project_root()
    session = start_session(cli, project_root)
    tasks = [
        asyncio.create_task(pty_reader(session, ws)),
        asyncio.create_task(ws_reader(ws, session)),
    ]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except Exception:
        pass
    finally:
        # Kill session first — closes master_fd so os.read() in executor unblocks immediately
        session.kill()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
