import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.backend.services.agent_service import pty_reader, start_session, ws_reader
from app.backend.services.file_service import get_project_root

router = APIRouter()


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
    try:
        await asyncio.gather(
            pty_reader(session, ws),
            ws_reader(ws, session),
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        session.kill()
