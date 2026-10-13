"""
File-based user repository.
Storage: backend/storage/users/{tenant_id}/users.json
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.paths import safe_tenant_id, storage_path
from app.core.filelock import atomic_write_json, file_lock, read_json
from app.models.user import User


class DuplicateEmailError(ValueError):
    pass


def _users_file(tenant_id: str) -> Path:
    path = storage_path("users", safe_tenant_id(tenant_id))
    path.mkdir(parents=True, exist_ok=True)
    return path / "users.json"


def _load(tenant_id: str) -> list[dict]:
    # Nunca devolver [] ante un archivo dañado: el siguiente alta borraría a todos los usuarios.
    return read_json(_users_file(tenant_id), list)


def _save(tenant_id: str, users: list[dict]) -> None:
    atomic_write_json(_users_file(tenant_id), users)


def get_by_email(email: str, tenant_id: str) -> Optional[User]:
    want = email.strip().lower()
    for u in _load(tenant_id):
        if (u.get("email") or "").strip().lower() == want:
            return User.from_dict(u)
    return None


def get_by_id(user_id: str, tenant_id: str) -> Optional[User]:
    want = str(user_id)
    for u in _load(tenant_id):
        if u.get("id") == want:
            return User.from_dict(u)
    return None


def create(user: User) -> User:
    with file_lock(_users_file(user.tenant_id)):
        users = _load(user.tenant_id)
        if any((u.get("email") or "").lower() == user.email for u in users):
            raise DuplicateEmailError("Email already registered")
        users.append(user.to_dict())
        _save(user.tenant_id, users)
    return user


def update(user_id: str, data: dict, tenant_id: str) -> Optional[User]:
    with file_lock(_users_file(tenant_id)):
        users = _load(tenant_id)
        for i, u in enumerate(users):
            if u.get("id") == str(user_id):
                users[i].update(data)
                _save(tenant_id, users)
                return User.from_dict(users[i])
    return None
