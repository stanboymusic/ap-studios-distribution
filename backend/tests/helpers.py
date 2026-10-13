"""Utilidades de tests: usuarios REALES en el almacén (el middleware verifica que existan y estén activos)."""
from __future__ import annotations

import uuid

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.repositories import user_repository as user_repo


def make_user(role: str = "artist", tenant: str = "default", uid: str | None = None, active: bool = True):
    uid = uid or str(uuid.uuid4())
    user = User(
        email=f"{uid}@test.io",
        hashed_password=hash_password("password-123"),
        role=role,
        tenant_id=tenant,
        id=uuid.UUID(uid),
        is_active=active,
    )
    user_repo.create(user)
    token = create_access_token(
        {"sub": uid, "role": role, "tenant_id": tenant, "email": user.email}
    )
    return uid, token


def auth(token: str, tenant: str = "default") -> dict:
    return {"Authorization": f"Bearer {token}", "X-Tenant-Id": tenant}
