"""
Auth context middleware.
Priority:
  1. Authorization: Bearer <jwt>  -> JWT verification
  2. X-User-Role + X-User-Id      -> legacy headers (dev/testing only)
  3. Nothing                      -> anonymous
"""
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token

VALID_ROLES = {"artist", "admin", "staff"}


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                request.state.user_id = payload.get("sub", "anonymous")
                request.state.user_role = payload.get("role", "artist")
                request.state.tenant_id = (
                    payload.get("tenant_id")
                    or request.headers.get("X-Tenant-Id")
                    or "default"
                )
                return await call_next(request)

        role = (request.headers.get("X-User-Role") or "artist").strip().lower()
        if role not in VALID_ROLES:
            role = "artist"
        user_id = (request.headers.get("X-User-Id") or "").strip()
        if not user_id:
            user_id = f"{role}:anonymous"

        request.state.user_role = role
        request.state.user_id = user_id
        return await call_next(request)
