import json
import logging
import traceback
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cv_backend.errors")


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
        except Exception as exc:
            entry = {
                "ts": datetime.now(UTC).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "traceback": traceback.format_exc(),
                "error": str(exc),
            }
            logger.error(json.dumps(entry))
            raise

        if response.status_code >= 400:
            entry = {
                "ts": datetime.now(UTC).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "traceback": None,
                "error": None,
            }
            logger.error(json.dumps(entry))

        return response
