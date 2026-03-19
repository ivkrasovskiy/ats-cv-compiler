from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.api import build, config, doctor, files, health, lint


def create_app() -> FastAPI:
    app = FastAPI(title="ats-cv-compiler", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(build.router, prefix="/api")
    app.include_router(lint.router, prefix="/api")
    app.include_router(doctor.router, prefix="/api")
    app.include_router(config.router, prefix="/api")

    # Serve built frontend in production (dist must exist)
    dist = Path("app/frontend/dist")
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")

    return app


app = create_app()


def start() -> None:
    import uvicorn

    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
