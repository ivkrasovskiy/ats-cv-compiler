import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.backend.services.build_service import (
    get_job,
    get_job_lines,
    start_build,
    start_build_from_md,
)

router = APIRouter()


class BuildRequest(BaseModel):
    job: str | None = None
    llm: str = "none"
    cover_letter: bool = False


@router.post("/build", status_code=202)
def post_build(req: BuildRequest) -> dict:
    job_id = start_build(req.job, req.llm, cover_letter=req.cover_letter)
    return {"job_id": job_id}


class BuildFromMdRequest(BaseModel):
    md_path: str


@router.post("/build/from-md", status_code=202)
def post_build_from_md(req: BuildFromMdRequest) -> dict:
    job_id = start_build_from_md(req.md_path)
    return {"job_id": job_id}


@router.get("/build/{job_id}")
def get_build_status(job_id: str) -> dict:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job not found: {job_id}")
    return {"job_id": job_id, "status": job["status"], "exit_code": job["exit_code"]}


@router.get("/build/{job_id}/stream")
async def stream_build_log(job_id: str) -> StreamingResponse:
    if get_job(job_id) is None:
        raise HTTPException(404, f"Job not found: {job_id}")

    async def event_generator():
        sent = 0
        while True:
            lines = get_job_lines(job_id)
            for line in lines[sent:]:
                yield f"data: {line}\n\n"
                sent += 1
            job = get_job(job_id)
            if job is not None and job["status"] != "running":
                yield "data: [DONE]\n\n"
                break
            await asyncio.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
