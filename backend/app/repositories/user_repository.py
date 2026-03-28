"""
File-based user repository.
Storage: backend/storage/users/{tenant_id}/users.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.core.paths import storage_path
from app.models.user import User


def _users_file(tenant_id: str) -> Path:
    path = storage_path("users", tenant_id)
    path.mkdir(parents=True, exist_ok=True)
    return path / "users.json"


def _load(tenant_id: str) -> list[dict]:
    f = _users_file(tenant_id)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tenant_id: str, users: list[dict]) -> None:
    _users_file(tenant_id).write_text(json.dumps(users, indent=2), encoding="utf-8")


def get_by_email(email: str, tenant_id: str) -> Optional[User]:
    want = email.strip().lower()
    for u in _load(tenant_id):
        if u.get("email") == want:
            return User.from_dict(u)
    return None


def get_by_id(user_id: str, tenant_id: str) -> Optional[User]:
    want = str(user_id)
    for u in _load(tenant_id):
        if u.get("id") == want:
            return User.from_dict(u)
    return None


def create(user: User) -> User:
    users = _load(user.tenant_id)
    users.append(user.to_dict())
    _save(user.tenant_id, users)
    return user


def update(user_id: str, data: dict, tenant_id: str) -> Optional[User]:
    users = _load(tenant_id)
    for i, u in enumerate(users):
        if u.get("id") == str(user_id):
            users[i].update(data)
            _save(tenant_id, users)
            return User.from_dict(users[i])
    return None
