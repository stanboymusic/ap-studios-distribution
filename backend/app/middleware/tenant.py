"""
Compatibilidad: el contexto de tenant ahora lo resuelve AuthContextMiddleware
a partir del JWT (nunca de un header controlado por el cliente).
Se conserva la clase para no romper imports existentes; no hace nada.
"""
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not getattr(request.state, "tenant_id", None):
            request.state.tenant_id = "default"
        return await call_next(request)
