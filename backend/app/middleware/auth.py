"""
Auth + tenant context middleware (único punto de entrada de identidad).

Reglas:
  * Toda ruta /api/* exige `Authorization: Bearer <jwt de acceso>`, salvo
    login / register / refresh.
  * user_id, rol y tenant salen EXCLUSIVAMENTE del JWT (firmado por el servidor).
    El header X-Tenant-Id ya no define el tenant: si viene y no coincide con el
    del token, se rechaza (403). Antes cualquiera podía cambiar de tenant o de
    rol con headers.
  * El rol y el estado activo se confirman contra el almacén de usuarios (con
    una caché corta), así un usuario desactivado o degradado pierde acceso rápido.
  * Los headers legacy X-User-Role / X-User-Id solo existen si
    AP_ALLOW_LEGACY_HEADERS=1 y APP_ENV != production (pruebas locales).
  * Rutas de administración se bloquean aquí también (defensa en profundidad).
"""
from __future__ import annotations

import os
import re
import threading
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.paths import is_valid_tenant_id
from app.core.security import decode_token

VALID_ROLES = {"artist", "admin", "staff"}
ADMIN_ROLES = {"admin", "staff"}

PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
}

# Rutas que solo puede usar el personal (admin/staff). Los artistas jamás las necesitan.
ADMIN_ONLY_PATTERNS = [
    re.compile(p)
    for p in (
        r"^/api/admin(/|$)",
        r"^/api/sandbox(/|$)",
        r"^/api/dsp(/|$)",
        r"^/api/delivery(/|$)",
        r"^/api/automation(/|$)",
        r"^/api/dsr(/|$)",            # ingesta de reportes de ventas = mueve dinero
        r"^/api/mwn(/|$)",
        r"^/api/mead(/|$)",
        r"^/api/ern/import(/|$)",
        r"^/api/analytics(/|$)",
        r"^/api/audio/fingerprint(/|$)",
        r"^/api/catalog/(identifiers|track|release)(/|$)",  # no confundir con /catalog/releases/{id}
    )
]

_STATE_TTL = 20.0
_state_cache: dict[tuple[str, str], tuple[float, Optional[dict]]] = {}
_state_lock = threading.Lock()


def invalidate_user_cache(user_id: Optional[str] = None) -> None:
    with _state_lock:
        if user_id is None:
            _state_cache.clear()
            return
        for key in [k for k in _state_cache if k[1] == str(user_id)]:
            _state_cache.pop(key, None)


def _legacy_headers_enabled() -> bool:
    if (os.getenv("APP_ENV") or "").strip().lower() in {"prod", "production"}:
        return False
    return (os.getenv("AP_ALLOW_LEGACY_HEADERS") or "").strip() in {"1", "true", "yes"}


def _lookup_user(tenant_id: str, user_id: str) -> Optional[dict]:
    now = time.time()
    key = (tenant_id, user_id)
    with _state_lock:
        hit = _state_cache.get(key)
        if hit and now - hit[0] < _STATE_TTL:
            return hit[1]
    from app.repositories import user_repository as user_repo  # import tardío (evita ciclos)

    try:
        user = user_repo.get_by_id(user_id, tenant_id)
    except Exception:
        user = None
    state = None if not user else {"role": user.role, "is_active": user.is_active}
    with _state_lock:
        _state_cache[key] = (now, state)
    return state


def _deny(status: int, detail: str, headers: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail}, headers=headers or {})


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Preflight CORS y rutas no-API (raíz, docs) pasan; el CORS middleware lo maneja.
        if request.method == "OPTIONS" or not path.startswith("/api"):
            request.state.user_id = "anonymous"
            request.state.user_role = "anonymous"
            request.state.tenant_id = "default"
            return await call_next(request)

        header_tenant = (request.headers.get("X-Tenant-Id") or "").strip()

        # --- Rutas públicas (login/registro/refresh): el tenant va en el cuerpo, no se confía en headers.
        if path.rstrip("/") in PUBLIC_API_PATHS:
            request.state.user_id = "anonymous"
            request.state.user_role = "anonymous"
            request.state.tenant_id = header_tenant if is_valid_tenant_id(header_tenant) else "default"
            return await call_next(request)

        # --- Autenticación por JWT
        auth_header = request.headers.get("Authorization", "")
        user_id = role = tenant_id = None

        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header[7:].strip())
            if not payload or payload.get("type") != "access":
                return _deny(401, "Invalid or expired token", {"WWW-Authenticate": "Bearer"})

            user_id = str(payload.get("sub") or "")
            role = str(payload.get("role") or "").lower()
            tenant_id = str(payload.get("tenant_id") or "")
            if not user_id or role not in VALID_ROLES or not is_valid_tenant_id(tenant_id):
                return _deny(401, "Invalid token claims", {"WWW-Authenticate": "Bearer"})

            if header_tenant and header_tenant != tenant_id:
                return _deny(403, "Tenant mismatch")

            if not user_id.startswith("system:"):
                state = _lookup_user(tenant_id, user_id)
                if state is None or not state["is_active"]:
                    return _deny(401, "Account not found or disabled", {"WWW-Authenticate": "Bearer"})
                role = state["role"]  # el rol vigente manda, no el del token
                if role not in VALID_ROLES:
                    return _deny(401, "Invalid role", {"WWW-Authenticate": "Bearer"})

        elif _legacy_headers_enabled():
            role = (request.headers.get("X-User-Role") or "artist").strip().lower()
            if role not in VALID_ROLES:
                role = "artist"
            user_id = (request.headers.get("X-User-Id") or "").strip() or f"{role}:anonymous"
            tenant_id = header_tenant if is_valid_tenant_id(header_tenant) else "default"
        else:
            return _deny(401, "Authentication required", {"WWW-Authenticate": "Bearer"})

        request.state.user_id = user_id
        request.state.user_role = role
        request.state.tenant_id = tenant_id

        if role not in ADMIN_ROLES and any(p.match(path) for p in ADMIN_ONLY_PATTERNS):
            return _deny(403, "Admin access required")

        return await call_next(request)
