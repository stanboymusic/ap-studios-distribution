from __future__ import annotations

import re
from pathlib import Path


# backend/app/core/paths.py -> parents[2] == <repo>/backend
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
STORAGE_DIR = BACKEND_DIR / "storage"
SANDBOX_DSP_DIR = REPO_DIR / "sandbox-dsp"

# Un tenant_id se usa como nombre de carpeta: solo caracteres seguros, sin
# separadores ni ".." (evita path traversal tipo X-Tenant-Id: ../../etc).
_TENANT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def is_valid_tenant_id(tenant_id: str | None) -> bool:
    return bool(tenant_id) and bool(_TENANT_RE.match(tenant_id or ""))


def safe_tenant_id(tenant_id: str | None) -> str:
    """Devuelve el tenant_id limpio o lanza ValueError si no es seguro."""
    value = (tenant_id or "").strip() or "default"
    if not _TENANT_RE.match(value):
        raise ValueError("Invalid tenant_id")
    return value


def storage_path(*parts: str) -> Path:
    return STORAGE_DIR.joinpath(*parts)


def tenant_root(tenant_id: str) -> Path:
    return storage_path("tenants", safe_tenant_id(tenant_id))


def tenant_path(tenant_id: str, *parts: str) -> Path:
    return tenant_root(tenant_id).joinpath(*parts)


def sandbox_dsp_path(*parts: str) -> Path:
    return SANDBOX_DSP_DIR.joinpath(*parts)
