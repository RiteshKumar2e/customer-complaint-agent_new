"""
In-process sliding-window rate limiter for per-IP request throttling.

This protects a single instance. Limits that must hold across instances and
restarts (OTP issuance, OTP verification failures, login lockout) are enforced
from Turso data in the auth services instead.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request

from app.core.errors import too_many


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> int:
        """Record a hit; return seconds to wait if over the limit, else 0."""
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] >= window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                return int(window_seconds - (now - bucket[0])) + 1
            bucket.append(now)
            if len(self._hits) > 50_000:  # bound memory under abuse
                self._prune(now, window_seconds)
            return 0

    def _prune(self, now: float, window_seconds: int) -> None:
        for key in [k for k, v in self._hits.items() if not v or now - v[-1] >= window_seconds]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, limit: int, window_seconds: int):
    """FastAPI dependency: at most `limit` requests per `window_seconds` per client IP."""

    def dependency(request: Request) -> None:
        wait = limiter.hit(f"{scope}:{client_ip(request)}", limit, window_seconds)
        if wait:
            raise too_many("Too many requests. Please slow down and try again shortly.", retry_after=wait)

    return dependency
