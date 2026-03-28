"""
Contract endpoints for AP Studios.
Artist accepts terms → recorded with timestamp, version, IP.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.contract import ContractAcceptance, CURRENT_CONTRACT_VERSION
from app.repositories import contract_repository as contract_repo

router = APIRouter(prefix="/contracts", tags=["Contracts"])
admin_router = APIRouter(prefix="/admin/contracts", tags=["Admin — Contracts"])


# ── Schemas ──────────────────────────────────────────────────────

class AcceptContractRequest(BaseModel):
    version: str = CURRENT_CONTRACT_VERSION
    # El artista confirma explícitamente que leyó y aceptó
    accepted: bool


class ContractResponse(BaseModel):
    id: str
    user_id: str
    version: str
    accepted_at: str
    ip_address: str | None
    has_accepted: bool
    is_current_version: bool


# ── Artist endpoints ─────────────────────────────────────────────

@router.post("/accept")
def accept_contract(body: AcceptContractRequest, request: Request):
    """Record contract acceptance for the authenticated artist."""
    if not body.accepted:
        raise HTTPException(
            status_code=400,
            detail="You must explicitly accept the terms (accepted=true)",
        )

    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", "default")

    if not user_id or user_id.endswith(":anonymous"):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Capturar IP real (considera proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else (request.client.host if request.client else None)
    )

    user_agent = request.headers.get("User-Agent", "")[:500]

    contract = ContractAcceptance(
        user_id=user_id,
        tenant_id=tenant_id,
        version=CURRENT_CONTRACT_VERSION,
        ip_address=ip,
        user_agent=user_agent,
    )
    contract_repo.save(contract)

    return {
        **contract.to_dict(),
        "has_accepted": True,
        "is_current_version": True,
    }


@router.get("/me")
def get_my_contract(request: Request):
    """Get current user's contract status."""
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", "default")

    if not user_id or user_id.endswith(":anonymous"):
        raise HTTPException(status_code=401, detail="Authentication required")

    contract = contract_repo.get_by_user_id(user_id, tenant_id)

    if not contract:
        return {
            "has_accepted": False,
            "is_current_version": False,
            "current_version": CURRENT_CONTRACT_VERSION,
        }

    return {
        **contract.to_dict(),
        "has_accepted": True,
        "is_current_version": contract.version == CURRENT_CONTRACT_VERSION,
        "current_version": CURRENT_CONTRACT_VERSION,
    }


# ── Admin endpoints ──────────────────────────────────────────────

@admin_router.get("")
def list_contracts(request: Request):
    """List all contract acceptances. Admin only."""
    role = getattr(request.state, "user_role", "artist")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    tenant_id = getattr(request.state, "tenant_id", "default")
    contracts = contract_repo.get_all(tenant_id)

    # Enrich with user email
    from app.repositories import user_repository as user_repo

    enriched = []
    for c in contracts:
        user = user_repo.get_by_id(c.user_id, tenant_id)
        enriched.append(
            {
                **c.to_dict(),
                "email": user.email if user else "unknown",
                "is_current_version": c.version == CURRENT_CONTRACT_VERSION,
            }
        )

    return {
        "total": len(enriched),
        "current_version": CURRENT_CONTRACT_VERSION,
        "contracts": enriched,
    }


@admin_router.get("/{user_id}")
def get_user_contract(user_id: str, request: Request):
    """Get contract for a specific user. Admin only."""
    role = getattr(request.state, "user_role", "artist")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    tenant_id = getattr(request.state, "tenant_id", "default")
    contract = contract_repo.get_by_user_id(user_id, tenant_id)

    if not contract:
        return {
            "user_id": user_id,
            "has_accepted": False,
            "current_version": CURRENT_CONTRACT_VERSION,
        }

    return {
        **contract.to_dict(),
        "has_accepted": True,
        "is_current_version": contract.version == CURRENT_CONTRACT_VERSION,
    }
