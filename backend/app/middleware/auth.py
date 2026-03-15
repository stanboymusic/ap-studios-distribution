from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


VALID_ROLES = {"artist", "admin", "staff"}


class AuthContextMiddleware(BaseHTTPMiddleware):
    """
    Lightweight auth context from headers.

    Headers:
    - X-User-Role: artist|admin|staff
    - X-User-Id:   stable user identifier
    """

    async def dispatch(self, request: Request, call_next):
        role = (request.headers.get("X-User-Role") or "artist").strip().lower()
        if role not in VALID_ROLES:
            role = "artist"

        user_id = (request.headers.get("X-User-Id") or "").strip()
        if not user_id:
            user_id = f"{role}:anonymous"

        request.state.user_role = role
        request.state.user_id = user_id
        return await call_next(request)

