"""
Auth endpoints: register, login, refresh, me, logout.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.core.paths import is_valid_tenant_id
from app.core.ratelimit import client_ip, is_limited, record, reset
from app.repositories import user_repository as user_repo
from app.services.notification_service import notify_admin_new_artist, notify_welcome
from app.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

# Hash de relleno: login con email inexistente tarda lo mismo que uno real (evita enumerar cuentas por tiempo).
_DUMMY_HASH = hash_password("not-a-real-password")
LOGIN_MAX_FAILS = 5
LOGIN_WINDOW = 15 * 60
REGISTER_MAX = 10
REGISTER_WINDOW = 60 * 60

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "artist"
    tenant_id: str = "default"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
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
def register(body: RegisterRequest, request: Request):
    # El registro público SOLO crea artistas. admin/staff se crean con scripts/create_admin.py
    # o desde el panel de administración. (Antes se aceptaba "staff", que equivale a admin.)
    if body.role != "artist":
        raise HTTPException(
            status_code=403,
            detail="Admin and staff accounts cannot be created via public registration",
        )

    ip = client_ip(request)
    rl_key = f"register:{ip}"
    if is_limited(rl_key, REGISTER_MAX, REGISTER_WINDOW):
        raise HTTPException(status_code=429, detail="Too many registrations. Try again later.")

    tenant_id = (body.tenant_id or "default").strip()
    if not is_valid_tenant_id(tenant_id) or not TenantService.get_tenant(tenant_id):
        raise HTTPException(status_code=400, detail="Unknown tenant")

    record(rl_key, REGISTER_WINDOW)

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role="artist",
        tenant_id=tenant_id,
    )
    try:
        user_repo.create(user)
    except user_repo.DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Los correos son un extra: si fallan, la cuenta ya existe y no debe responder 500.
    try:
        notify_welcome(email=user.email, artist_name=user.email.split("@")[0])
        notify_admin_new_artist(
            artist_email=user.email,
            registered_at=user.created_at,
            tenant_id=user.tenant_id,
            contract_signed=False,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Registration notification failed: %s", exc)
    return _issue_tokens(user)


@router.post("/login")
def login(body: LoginRequest, request: Request):
    tenant_id = (body.tenant_id or "default").strip()
    email_key = body.email.strip().lower()
    rl_key = f"login:{client_ip(request)}:{tenant_id}:{email_key}"
    if is_limited(rl_key, LOGIN_MAX_FAILS, LOGIN_WINDOW):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a few minutes.")

    user = user_repo.get_by_email(body.email, tenant_id) if is_valid_tenant_id(tenant_id) else None
    ok = verify_password(body.password, user.hashed_password if user else _DUMMY_HASH)
    if not user or not ok:
        record(rl_key, LOGIN_WINDOW)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    reset(rl_key)
    return _issue_tokens(user)


@router.post("/refresh")
def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    tenant_id = payload.get("tenant_id", "default")
    user = user_repo.get_by_id(payload["sub"], tenant_id) if is_valid_tenant_id(tenant_id) else None
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
