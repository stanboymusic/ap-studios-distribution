from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant context:
    - Requires `X-Tenant-Id` header on every /api request.
    - Sets `request.state.tenant_id`.
    """

    async def dispatch(self, request: Request, call_next):
        # Only enforce for API routes
        if request.url.path.startswith("/api"):
            # Bootstrap endpoints must work without an existing tenant context.
            # Swagger UI also won't include custom headers by default.
            if request.url.path.startswith("/api/tenants"):
                request.state.tenant_id = request.headers.get("X-Tenant-Id") or "default"
                return await call_next(request)
            # Internal tooling endpoints: allow default tenant for convenience in docs/testing.
            if request.url.path.startswith("/api/sandbox") or request.url.path.startswith("/api/dsp"):
                request.state.tenant_id = request.headers.get("X-Tenant-Id") or "default"
                return await call_next(request)

            tenant_id = request.headers.get("X-Tenant-Id")
            if not tenant_id:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Tenant not specified. Provide X-Tenant-Id header."},
                )
            request.state.tenant_id = tenant_id
        return await call_next(request)
