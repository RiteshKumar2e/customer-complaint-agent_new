"""ASGI middleware: request ids, body-size limits, security headers."""
from __future__ import annotations

import json
import time
import uuid

from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, log_event, request_id_var

logger = get_logger("app.http")


class RequestContextMiddleware:
    """Assigns a request id, enforces a maximum body size and adds security headers."""

    def __init__(self, app, max_body_bytes: int, upload_paths_max_bytes: int, upload_path_suffix: str = "/attachments"):
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.upload_max = upload_paths_max_bytes
        self.upload_suffix = upload_path_suffix

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:16]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        path = scope.get("path", "")
        limit = self.upload_max + 64_000 if path.endswith(self.upload_suffix) else self.max_body_bytes

        headers = dict(scope.get("headers") or [])
        declared = headers.get(b"content-length")
        if declared is not None:
            try:
                too_big = int(declared) > limit
            except ValueError:
                too_big = True
            if too_big:
                await self._reject(send, request_id)
                request_id_var.reset(token)
                return

        received = 0
        status_holder = {"status": 500}

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise _BodyTooLarge()
            return message

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                extra = [
                    (b"x-request-id", request_id.encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"cross-origin-resource-policy", b"cross-origin"),
                    (b"cache-control", b"no-store"),
                ]
                existing = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [h for h in extra if h[0] not in existing]
            await send(message)

        try:
            await self.app(scope, limited_receive, send_wrapper)
        except _BodyTooLarge:
            await self._reject(send, request_id)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            if path not in ("/health", "/"):
                log_event(logger, 20, "request", method=scope.get("method"), path=path,
                          status=status_holder["status"], duration_ms=duration_ms)
            request_id_var.reset(token)

    @staticmethod
    async def _reject(send, request_id: str) -> None:
        body = json.dumps({"detail": "Request body is too large.", "code": "PAYLOAD_TOO_LARGE",
                           "request_id": request_id}).encode()
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


class _BodyTooLarge(StarletteHTTPException):
    """Raised from receive(); an HTTPException so FastAPI's body parser re-raises it as-is."""

    def __init__(self) -> None:
        super().__init__(status_code=413, detail="Request body is too large.")
