"""Límite simple de intentos en memoria (por proceso). Suficiente contra fuerza bruta básica;
para varios workers/réplicas conviene moverlo a Redis."""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

_lock = threading.Lock()
_events: dict[str, deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    if (os.getenv("TRUST_PROXY") or "").strip() in {"1", "true", "yes"}:
        fwd = request.headers.get("X-Forwarded-For")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune(dq: deque, window: float, now: float) -> None:
    while dq and now - dq[0] > window:
        dq.popleft()


def is_limited(key: str, limit: int, window_seconds: float) -> bool:
    now = time.time()
    with _lock:
        dq = _events[key]
        _prune(dq, window_seconds, now)
        return len(dq) >= limit


def record(key: str, window_seconds: float) -> None:
    now = time.time()
    with _lock:
        dq = _events[key]
        _prune(dq, window_seconds, now)
        dq.append(now)


def reset(key: str) -> None:
    with _lock:
        _events.pop(key, None)
