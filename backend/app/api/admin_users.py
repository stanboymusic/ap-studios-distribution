"""
Admin-only endpoints for user management.
All endpoints require role=admin verified via JWT.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.repositories import user_repository as user_repo
from app.services.catalog_service import CatalogService
from app.services.notification_service import notify_account_status_changed

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


def _require_admin(request: Request):
    """Raise 403 if caller is not admin."""
    role = getattr(request.state, "user_role", "artist")
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )


def _get_tenant(request: Request) -> str:
    return (
        getattr(request.state, "tenant_id", None)
        or request.headers.get("X-Tenant-Id", "default")
    )


# -- Pydantic schemas --

class PatchUserRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    artist_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str
    artist_id: Optional[str]
    is_active: bool
    created_at: Optional[str]
    release_count: int = 0


# -- Helpers --

def _enrich_user(user, tenant_id: str) -> dict:
    """Add release_count to user dict."""
    try:
        releases = CatalogService.get_releases(tenant_id=tenant_id)
        release_count = sum(
            1
            for r in releases
            if getattr(r, "owner_user_id", None) == str(user.id)
        )
    except Exception:
        release_count = 0

    data = user.to_public()
    data["release_count"] = release_count
    return data


# -- Endpoints --

@router.get("")
def list_users(request: Request):
    """List all registered users. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    from app.repositories.user_repository import _load
    raw_users = _load(tenant_id)

    from app.models.user import User
    users = [User.from_dict(u) for u in raw_users]

    return {
        "total": len(users),
        "users": [_enrich_user(u, tenant_id) for u in users],
    }


@router.get("/{user_id}")
def get_user(user_id: str, request: Request):
    """Get a single user by ID. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    user = user_repo.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _enrich_user(user, tenant_id)


@router.patch("/{user_id}")
def patch_user(user_id: str, body: PatchUserRequest, request: Request):
    """Update user is_active or role. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    user = user_repo.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    caller_id = getattr(request.state, "user_id", None)
    if str(user.id) == caller_id and body.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account",
        )

    # Prevent changing the role TO admin via API
    if body.role and body.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot assign admin role via API",
        )

    updates = {}
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if body.role is not None:
        updates["role"] = body.role
    if body.artist_id is not None:
        updates["artist_id"] = body.artist_id

    if not updates:
        return _enrich_user(user, tenant_id)

    updated = user_repo.update(user_id, updates, tenant_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")

    if body.is_active is not None and body.is_active != user.is_active:
        notify_account_status_changed(
            email=updated.email,
            artist_name=updated.email.split("@")[0],
            is_active=updated.is_active,
        )

    return _enrich_user(updated, tenant_id)


@router.get("/{user_id}/releases")
def get_user_releases(user_id: str, request: Request):
    """Get all releases owned by a user. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    user = user_repo.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    releases = CatalogService.get_releases(tenant_id=tenant_id)
    user_releases = [
        r for r in releases
        if getattr(r, "owner_user_id", None) == user_id
    ]

    def release_to_dict(r):
        return {
            "id": str(getattr(r, "id", "") or getattr(r, "release_id", "")),
            "title": getattr(r, "title", ""),
            "status": getattr(r, "status", ""),
            "release_type": str(getattr(r, "release_type", "")),
            "upc": getattr(r, "upc", None),
            "created_at": str(getattr(r, "created_at", "") or ""),
        }

    return {
        "user_id": user_id,
        "email": user.email,
        "total": len(user_releases),
        "releases": [release_to_dict(r) for r in user_releases],
    }
