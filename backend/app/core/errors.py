"""
Centralised exception handling.

Every error response has the same shape:
    {"detail": "<human readable>", "code": "<MACHINE_CODE>", "request_id": "...", "errors": [...]?}

`detail` stays a string so existing clients reading `response.data.detail`
keep working. Stack traces, SQL and driver messages are never returned.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError, TimeoutError as PoolTimeout
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, request_id_var

logger = get_logger("app.errors")


class AppError(Exception):
    def __init__(self, status_code: int, message: str, code: str = "ERROR", errors: Optional[List[Any]] = None,
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.errors = errors
        self.headers = headers


def bad_request(message: str, code: str = "BAD_REQUEST") -> AppError:
    return AppError(400, message, code)


def unauthorized(message: str = "Authentication required", code: str = "UNAUTHORIZED") -> AppError:
    return AppError(401, message, code, headers={"WWW-Authenticate": "Bearer"})


def forbidden(message: str = "You do not have permission to perform this action", code: str = "FORBIDDEN") -> AppError:
    return AppError(403, message, code)


def not_found(message: str = "Not found", code: str = "NOT_FOUND") -> AppError:
    return AppError(404, message, code)


def conflict(message: str, code: str = "CONFLICT") -> AppError:
    return AppError(409, message, code)


def too_many(message: str, retry_after: Optional[int] = None, code: str = "RATE_LIMITED") -> AppError:
    headers = {"Retry-After": str(max(1, int(retry_after)))} if retry_after else None
    return AppError(429, message, code, headers=headers)


def unavailable(message: str, code: str = "SERVICE_UNAVAILABLE") -> AppError:
    return AppError(503, message, code)


_HTTP_CODES = {
    400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE", 415: "UNSUPPORTED_MEDIA_TYPE", 422: "VALIDATION_ERROR",
    429: "RATE_LIMITED", 500: "INTERNAL_ERROR", 503: "SERVICE_UNAVAILABLE",
}


def error_body(message: str, code: str, errors: Optional[List[Any]] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"detail": message, "code": code, "request_id": request_id_var.get()}
    if errors:
        body["errors"] = errors
    return body


_FIELD_LABELS = {"phone": "Mobile number", "email": "Email", "full_name": "Full name", "password": "Password",
                 "otp": "Verification code", "new_password": "New password"}


def _format_validation_errors(exc: RequestValidationError) -> List[Dict[str, str]]:
    formatted = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path")]
        message = str(err.get("msg", "Invalid value"))
        if message.startswith("Value error, "):
            message = message[len("Value error, "):]
        field = ".".join(loc) or "request"
        if err.get("type") == "missing":
            message = f"{_FIELD_LABELS.get(field, field.replace('_', ' ').capitalize())} is required"
        formatted.append({"field": field, "message": message})
    return formatted


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.message, exc.code, exc.errors),
                            headers=exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(status_code=exc.status_code,
                            content=error_body(message, _HTTP_CODES.get(exc.status_code, "ERROR")),
                            headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        # The request body is deliberately NOT echoed back: it can contain passwords.
        errors = _format_validation_errors(exc)
        summary = errors[0]["message"] if len(errors) == 1 else "Some fields are invalid"
        return JSONResponse(status_code=422, content=error_body(summary, "VALIDATION_ERROR", errors))

    @app.exception_handler(OperationalError)
    @app.exception_handler(PoolTimeout)
    async def _db_unavailable(request: Request, exc: Exception):
        logger.error("Database unavailable: %s", type(exc).__name__, exc_info=exc)
        return JSONResponse(status_code=503, content=error_body(
            "The database is temporarily unavailable. Please try again shortly.", "DATABASE_UNAVAILABLE"),
            headers={"Retry-After": "5"})

    @app.exception_handler(DBAPIError)
    @app.exception_handler(SQLAlchemyError)
    async def _db_error(request: Request, exc: Exception):
        logger.error("Database error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content=error_body("A database error occurred.", "DATABASE_ERROR"))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.log(logging.ERROR, "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content=error_body("An unexpected error occurred.", "INTERNAL_ERROR"))
