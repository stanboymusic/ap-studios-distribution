"""
Auth endpoints: register, login, refresh, me, logout.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.repositories import user_repository as user_repo
from app.services.notification_service import notify_admin_new_artist, notify_welcome

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "artist"
    tenant_id: str = "default"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str = "default"


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_tokens(user: User) -> dict:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
    }
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
        "user": user.to_public(),
    }


@router.post("/register")
def register(body: RegisterRequest):
    # Solo se permite registrar artistas desde la API pública
    # El rol "admin" solo se puede crear via create_admin.py script
    ALLOWED_PUBLIC_ROLES = {"artist", "staff"}
    if body.role not in ALLOWED_PUBLIC_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Role 'admin' cannot be created via public registration",
        )

    existing = user_repo.get_by_email(body.email, body.tenant_id)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        tenant_id=body.tenant_id,
    )
    user_repo.create(user)
    notify_welcome(email=user.email, artist_name=user.email.split("@")[0])
    notify_admin_new_artist(
        artist_email=user.email,
        registered_at=user.created_at,
        tenant_id=user.tenant_id,
        contract_signed=False,
    )
    return _issue_tokens(user)


@router.post("/login")
def login(body: LoginRequest):
    user = user_repo.get_by_email(body.email, body.tenant_id)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return _issue_tokens(user)


@router.post("/refresh")
def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = user_repo.get_by_id(payload["sub"], payload.get("tenant_id", "default"))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")

    return {
        "access_token": create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "tenant_id": user.tenant_id,
            }
        ),
        "token_type": "bearer",
    }


@router.get("/me")
def me(request: Request):
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", "default")
    role = getattr(request.state, "user_role", None)

    if not user_id or user_id.endswith(":anonymous"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = user_repo.get_by_id(user_id, tenant_id)
    if not user:
        return {"id": user_id, "role": role, "tenant_id": tenant_id}

    return user.to_public()


@router.post("/logout")
def logout(_request: Request):
    return {"status": "logged_out"}
