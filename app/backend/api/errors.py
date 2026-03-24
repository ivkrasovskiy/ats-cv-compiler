import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["errors"])

logger = logging.getLogger("cv_backend.frontend_errors")


class ClientError(BaseModel):
    message: str
    stack: str | None = None
    component_stack: str | None = None
    url: str | None = None


@router.post("/client-errors")
async def log_client_error(error: ClientError):
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "source": "frontend",
        "message": error.message,
        "stack": error.stack,
        "component_stack": error.component_stack,
        "url": error.url,
    }
    logger.error(json.dumps(entry))
    return {"ok": True}
