"""
Alta del usuario admin inicial.
Ejecutar: python backend/scripts/create_admin.py
También se llama desde main.py al arrancar (solo crea el admin si NO existe ninguno).

Seguridad:
  * Ya no existe contraseña por defecto en el código (antes era pública en el repo).
  * AP_ADMIN_PASSWORD (mín. 12 caracteres) define la clave. Si falta:
      - desarrollo: se genera una clave aleatoria y se muestra UNA vez en consola.
      - producción (APP_ENV=production): no se crea el admin y se avisa en el log.
  * Nunca se promueve a admin una cuenta ya existente (alguien podría haberse registrado
    antes con ese correo).
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repository as user_repo

DEFAULT_EMAIL = os.getenv("AP_ADMIN_EMAIL", "admin@apstudios.io")
DEFAULT_TENANT = "default"


def create_admin_if_missing():
    existing = user_repo.get_by_email(DEFAULT_EMAIL, DEFAULT_TENANT)
    if existing:
        if existing.role != "admin":
            print(
                f"[seed] AVISO: {DEFAULT_EMAIL} ya existe con rol '{existing.role}'. "
                "No se promueve automáticamente. Cámbialo manualmente si es tu cuenta."
            )
        else:
            print(f"[seed] Admin ya existe: {DEFAULT_EMAIL}")
        return

    password = (os.getenv("AP_ADMIN_PASSWORD") or "").strip()
    is_prod = (os.getenv("APP_ENV") or "").strip().lower() in {"prod", "production"}
    generated = False
    if not password:
        if is_prod:
            print("[seed] No se creó el admin: define AP_ADMIN_PASSWORD (mín. 12 caracteres).")
            return
        password = secrets.token_urlsafe(16)
        generated = True
    elif len(password) < 12:
        print("[seed] No se creó el admin: AP_ADMIN_PASSWORD debe tener al menos 12 caracteres.")
        return

    user = User(
        email=DEFAULT_EMAIL,
        hashed_password=hash_password(password),
        role="admin",
        tenant_id=DEFAULT_TENANT,
    )
    try:
        user_repo.create(user)
    except user_repo.DuplicateEmailError:
        return
    print(f"[seed] Admin creado: {DEFAULT_EMAIL}")
    if generated:
        print(f"[seed] Contraseña temporal (guárdala ahora, no se vuelve a mostrar): {password}")


if __name__ == "__main__":
    create_admin_if_missing()
