"""
Seed del usuario admin inicial.
Ejecutar: python backend/scripts/create_admin.py
También se llama desde main.py al arrancar.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repository as user_repo

DEFAULT_EMAIL = os.getenv("AP_ADMIN_EMAIL", "admin@apstudios.io")
DEFAULT_PASSWORD = os.getenv("AP_ADMIN_PASSWORD", "apstudios2024!")
DEFAULT_TENANT = "default"


def create_admin_if_missing():
    existing = user_repo.get_by_email(DEFAULT_EMAIL, DEFAULT_TENANT)
    if existing:
        if existing.role != "admin":
            user_repo.update(str(existing.id), {"role": "admin"}, DEFAULT_TENANT)
            print(f"[seed] Admin role fixed: {DEFAULT_EMAIL}")
        else:
            print(f"[seed] Admin ya existe correctamente: {DEFAULT_EMAIL}")
        return
    user = User(
        email=DEFAULT_EMAIL,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        role="admin",
        tenant_id=DEFAULT_TENANT,
    )
    user_repo.create(user)
    print(f"[seed] Admin creado: {DEFAULT_EMAIL}")


if __name__ == "__main__":
    create_admin_if_missing()
