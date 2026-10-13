from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any

from app.core.auth import is_admin, require_admin
from app.core.paths import is_valid_tenant_id
from app.services.tenant_service import TenantService


router = APIRouter(prefix="/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    id: str
    name: str


@router.get("/", response_model=List[Dict[str, Any]])
def list_tenants(request: Request):
    require_admin(request)  # antes: cualquiera podía listar todos los tenants
    TenantService.ensure_default_tenant()
    return TenantService.list_tenants()


@router.post("/")
def create_tenant(payload: TenantCreate, request: Request):
    require_admin(request)  # antes: cualquiera podía crear tenants
    if not is_valid_tenant_id(payload.id):
        raise HTTPException(status_code=400, detail="Invalid tenant id (letters, numbers, - and _ only)")
    t = TenantService.create_tenant(payload.id, payload.name)
    return t


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str, request: Request):
    # Un artista solo puede consultar SU tenant.
    if not is_admin(request) and tenant_id != request.state.tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t = TenantService.get_tenant(tenant_id) if is_valid_tenant_id(tenant_id) else None
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t
