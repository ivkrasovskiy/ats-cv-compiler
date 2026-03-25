from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.api import (
    agent,
    build,
    config,
    doctor,
    errors,
    files,
    form,
    health,
    lint,
    repair,
    system,
)
from app.backend.middleware.error_logging import ErrorLoggingMiddleware
from app.backend.services.log_service import cleanup_old_logs, setup_logging


def _log_dir() -> Path:
    from app.backend.services.file_service import get_project_root

    return get_project_root() / "logs"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_dir = _log_dir()
    setup_logging(log_dir)
    cleanup_old_logs(log_dir)

    # Start repair background task
    import asyncio

    from app.backend.services.file_service import get_project_root
    from app.backend.services.repair_service import repair_loop

    task = asyncio.create_task(repair_loop(log_dir, get_project_root()))
    yield
    # Signal SSE generators to exit immediately (unblocks uvicorn graceful shutdown)
    from app.backend.services.repair_service import signal_shutdown

    signal_shutdown()
    # Cancel repair loop, kill all open PTY sessions
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    from app.backend.services.agent_service import shutdown_all_sessions

    shutdown_all_sessions()


def create_app() -> FastAPI:
    app = FastAPI(title="ats-cv-compiler", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ErrorLoggingMiddleware)

    app.include_router(health.router, prefix="/api")
    app.include_router(form.router, prefix="/api")  # must be before files (more specific routes)
    app.include_router(files.router, prefix="/api")
    app.include_router(build.router, prefix="/api")
    app.include_router(lint.router, prefix="/api")
    app.include_router(doctor.router, prefix="/api")
    app.include_router(config.router, prefix="/api")
    app.include_router(errors.router)
    app.include_router(repair.router)
    app.include_router(system.router)
    app.include_router(agent.router)  # WebSocket at /ws/agent (no /api prefix)

    # Serve built frontend in production (dist must exist)
    dist = Path("app/frontend/dist")
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")

    return app


app = create_app()


def start() -> None:
    import uvicorn

    uvicorn.run(
        "app.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_graceful_shutdown=5,  # force-close lingering connections after 5s on reload
    )


if __name__ == "__main__":
    start()
