from __future__ import annotations

from pathlib import Path


# backend/app/core/paths.py -> parents[2] == <repo>/backend
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
STORAGE_DIR = BACKEND_DIR / "storage"
SANDBOX_DSP_DIR = REPO_DIR / "sandbox-dsp"


def storage_path(*parts: str) -> Path:
    return STORAGE_DIR.joinpath(*parts)

def tenant_root(tenant_id: str) -> Path:
    safe = (tenant_id or "").strip()
    if not safe:
        safe = "default"
    return storage_path("tenants", safe)


def tenant_path(tenant_id: str, *parts: str) -> Path:
    return tenant_root(tenant_id).joinpath(*parts)


def sandbox_dsp_path(*parts: str) -> Path:
    return SANDBOX_DSP_DIR.joinpath(*parts)
