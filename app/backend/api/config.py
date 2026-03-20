from typing import Annotated

from fastapi import APIRouter, Body, HTTPException

from app.backend.services.config_service import read_config, write_config

router = APIRouter()


@router.get("/config")
def get_config() -> dict:
    try:
        return read_config()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.put("/config")
def put_config(body: Annotated[dict, Body()]) -> dict:
    try:
        write_config(body)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    return {"saved": True}
