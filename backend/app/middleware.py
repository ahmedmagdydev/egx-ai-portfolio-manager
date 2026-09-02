from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from .logging import correlation_id_var, log_request


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        token = correlation_id_var.set(correlation_id)
        started = perf_counter()
        try:
            response = await call_next(request)
            log_request(
                level="INFO",
                route=request.url.path,
                duration_ms=(perf_counter() - started) * 1000,
            )
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        except Exception:
            log_request(
                level="ERROR",
                route=request.url.path,
                duration_ms=(perf_counter() - started) * 1000,
                error_code="INTERNAL_ERROR",
            )
            raise
        finally:
            correlation_id_var.reset(token)
