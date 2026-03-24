import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.backend.services import repair_service
from app.backend.services.file_service import get_project_root

router = APIRouter(prefix="/api/repair", tags=["repair"])


async def _sse_generator() -> AsyncGenerator[str, None]:
    queue = repair_service.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except TimeoutError:
                yield ": heartbeat\n\n"
    finally:
        repair_service.unsubscribe(queue)


@router.get("/stream")
async def repair_stream():
    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status")
async def repair_status():
    from app.backend.services.github_service import gh_available

    event = repair_service.get_latest_event()
    return {
        "event": repair_service._event_to_dict(event) if event else None,
        "gh_available": gh_available(),
    }


class ApplyRequest(BaseModel):
    event_id: str | None = None


@router.post("/apply")
async def repair_apply():
    event = repair_service.get_latest_event()
    if not event:
        return {"ok": False, "message": "No repair event available"}

    project_root = get_project_root()
    output = await asyncio.get_event_loop().run_in_executor(
        None,
        repair_service.apply_fix,
        repair_service.ErrorEntry(
            ts=event.error_entry["ts"],
            method=event.error_entry["method"],
            path=event.error_entry["path"],
            status=event.error_entry["status"],
            traceback=event.error_entry.get("traceback"),
            error=event.error_entry.get("error"),
        ),
        event.fix_hint,
        project_root,
    )
    event.status = "fix_applied"
    event.fix_output = output
    await repair_service._broadcast(
        {"type": "fix_applied", "event": repair_service._event_to_dict(event)}
    )
    return {"ok": True, "output": output}


@router.post("/dismiss")
async def repair_dismiss():
    event = repair_service.get_latest_event()
    if event:
        event.status = "dismissed"
    return {"ok": True}


class GithubIssueRequest(BaseModel):
    title: str
    body: str


@router.post("/github-issue")
async def repair_github_issue(req: GithubIssueRequest):
    from app.backend.services.github_service import create_issue, gh_available

    if not gh_available():
        return {"ok": False, "message": "gh CLI not found on PATH"}

    try:
        url = create_issue(req.title, req.body)
        event = repair_service.get_latest_event()
        if event:
            event.gh_issue_url = url
        return {"ok": True, "url": url}
    except RuntimeError as exc:
        return {"ok": False, "message": str(exc)}
