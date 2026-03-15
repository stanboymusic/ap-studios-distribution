from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.tenant_service import TenantService


router = APIRouter(prefix="/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    id: str
    name: str


@router.get("/", response_model=List[Dict[str, Any]])
def list_tenants():
    TenantService.ensure_default_tenant()
    return TenantService.list_tenants()


@router.post("/")
def create_tenant(payload: TenantCreate):
    if not payload.id:
        raise HTTPException(status_code=400, detail="id is required")
    t = TenantService.create_tenant(payload.id, payload.name)
    return t


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str):
    t = TenantService.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t
