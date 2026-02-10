"""Generic HTTP error handling middleware for FastAPI and aiohttp."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from orchid_commons.observability.logging import get_correlation_ids
from orchid_commons.runtime.errors import OrchidCommonsError

logger = logging.getLogger(__name__)

ExceptionHandler: TypeAlias = tuple[type[Exception], Callable[[Exception], "ErrorResponse"]]
FastApiCallNext: TypeAlias = Callable[[Any], Awaitable[Any]]
AiohttpHandler: TypeAlias = Callable[[Any], Awaitable[Any]]


class APIError(OrchidCommonsError):
    """Base API error with code and details."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


@dataclass(frozen=True)
class ErrorResponse:
    """Describes how to render an exception as an HTTP error."""

    code: str
    message: str
    status_code: int = 400
    details: dict[str, Any] = field(default_factory=dict)
    log_level: int = logging.WARNING


def _resolve_request_id(request: Any) -> str:
    """Extract request ID from request state, correlation context, or fallback."""
    # Try request.state.request_id (FastAPI)
    state = getattr(request, "state", None)
    if state is not None:
        req_id = getattr(state, "request_id", None)
        if req_id is not None:
            return str(req_id)

    # Try aiohttp dict-style
    if isinstance(request, dict):
        req_id = request.get("request_id")
        if req_id is not None:
            return str(req_id)

    # Try correlation context
    try:
        correlation = get_correlation_ids()
        if correlation.request_id is not None:
            return correlation.request_id
    except Exception:
        pass

    return "unknown"


def _build_error_body(
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    """Build the standard error response body."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


def _dispatch_exception(
    exc: Exception,
    handlers: Sequence[ExceptionHandler],
    catch_all_message: str,
) -> ErrorResponse:
    """Match an exception to a handler and return an ErrorResponse."""
    if isinstance(exc, APIError):
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        return ErrorResponse(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            log_level=log_level,
        )

    for exc_type, handler in handlers:
        if isinstance(exc, exc_type):
            return handler(exc)

    return ErrorResponse(
        code="INTERNAL_ERROR",
        message=catch_all_message,
        status_code=500,
        details={},
        log_level=logging.CRITICAL,
    )


def _log_error(error_response: ErrorResponse, exc: Exception) -> None:
    """Log the error at the appropriate level."""
    if error_response.log_level == logging.CRITICAL:
        # Catch-all: log with full traceback
        logger.error(
            "Unexpected error: %s",
            exc,
            exc_info=True,
            extra={
                "error_code": error_response.code,
                "status_code": error_response.status_code,
                "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__),
            },
        )
    elif error_response.status_code >= 500:
        logger.error(
            "Server error: %s — %s",
            error_response.code,
            error_response.message,
            extra={
                "error_code": error_response.code,
                "status_code": error_response.status_code,
            },
        )
    else:
        logger.warning(
            "Client error: %s — %s",
            error_response.code,
            error_response.message,
            extra={
                "error_code": error_response.code,
                "status_code": error_response.status_code,
            },
        )


def create_fastapi_error_middleware(
    handlers: Sequence[ExceptionHandler] = (),
    catch_all_message: str = "An unexpected error occurred",
) -> Callable[[Any, FastApiCallNext], Awaitable[Any]]:
    """Build FastAPI middleware that catches exceptions and returns JSON error responses."""

    async def middleware(request: Any, call_next: FastApiCallNext) -> Any:
        try:
            return await call_next(request)
        except Exception as exc:
            error_response = _dispatch_exception(exc, handlers, catch_all_message)
            _log_error(error_response, exc)
            request_id = _resolve_request_id(request)
            body = _build_error_body(
                request_id,
                error_response.code,
                error_response.message,
                error_response.details,
            )
            # Import here to avoid hard dependency at module level
            try:
                from starlette.responses import JSONResponse
            except ImportError:
                from json import dumps

                class _MinimalJSON:  # type: ignore[no-redef]
                    def __init__(self, content: Any, status_code: int) -> None:
                        self.status_code = status_code
                        self.body = dumps(content).encode()

                return _MinimalJSON(content=body, status_code=error_response.status_code)  # type: ignore[return-value]
            return JSONResponse(status_code=error_response.status_code, content=body)

    return middleware


def create_aiohttp_error_middleware(
    handlers: Sequence[ExceptionHandler] = (),
    catch_all_message: str = "An unexpected error occurred",
    decorate: bool = True,
) -> Callable[[Any, AiohttpHandler], Awaitable[Any]]:
    """Build aiohttp middleware that catches exceptions and returns JSON error responses."""

    async def middleware(request: Any, handler: AiohttpHandler) -> Any:
        try:
            return await handler(request)
        except Exception as exc:
            error_response = _dispatch_exception(exc, handlers, catch_all_message)
            _log_error(error_response, exc)
            request_id = _resolve_request_id(request)
            body = _build_error_body(
                request_id,
                error_response.code,
                error_response.message,
                error_response.details,
            )
            try:
                from aiohttp import web

                return web.json_response(body, status=error_response.status_code)
            except ImportError:
                from json import dumps

                class _MinimalJSON:  # type: ignore[no-redef]
                    def __init__(self, content: Any, status_code: int) -> None:
                        self.status = status_code
                        self.body = dumps(content).encode()

                return _MinimalJSON(content=body, status_code=error_response.status_code)  # type: ignore[return-value]

    if decorate:
        try:
            from aiohttp import web

            return web.middleware(middleware)  # type: ignore[return-value]
        except ImportError:
            pass
    return middleware


__all__ = [
    "APIError",
    "ErrorResponse",
    "ExceptionHandler",
    "create_aiohttp_error_middleware",
    "create_fastapi_error_middleware",
]
