"""System control endpoints: shutdown and restart the backend process."""

import os
import signal
import sys
import threading

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])


def _shutdown_after(delay: float = 0.5) -> None:
    """Send SIGTERM to self after a short delay (lets the HTTP response flush)."""

    def _do():
        import time

        time.sleep(delay)
        os.kill(os.getpid(), signal.SIGTERM)

    t = threading.Thread(target=_do, daemon=True)
    t.start()


def _restart_after(delay: float = 0.5) -> None:
    """Re-exec the current process. Works with uvicorn reload mode too."""

    def _do():
        import time

        time.sleep(delay)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    t = threading.Thread(target=_do, daemon=True)
    t.start()


@router.post("/shutdown")
async def shutdown():
    """Gracefully shut down the backend (and therefore the whole app started via start.sh)."""
    _shutdown_after()
    return {"ok": True, "message": "Shutting down…"}


@router.post("/restart")
async def restart():
    """Re-exec the backend process (uvicorn reload picks up the new process)."""
    _restart_after()
    return {"ok": True, "message": "Restarting…"}
