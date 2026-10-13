"""
JWT security utilities for AP Studios.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

def _load_secret_key() -> str:
    """
    Clave de firma de los JWT.
    - Producción: AP_SECRET_KEY es obligatoria (si no, tokens distintos por proceso
      y reinicio => sesiones rotas y el worker no puede autenticarse).
    - Desarrollo: si falta, se genera UNA vez y se guarda en storage/.dev_secret_key.
    """
    env_key = (os.getenv("AP_SECRET_KEY") or "").strip()
    if env_key:
        if len(env_key) < 32:
            raise RuntimeError("AP_SECRET_KEY must be at least 32 characters")
        return env_key
    if (os.getenv("APP_ENV") or "").strip().lower() in {"prod", "production"}:
        raise RuntimeError("AP_SECRET_KEY is required when APP_ENV=production")

    from app.core.paths import storage_path

    key_file = storage_path(".dev_secret_key")
    try:
        if key_file.exists():
            value = key_file.read_text(encoding="utf-8").strip()
            if len(value) >= 32:
                return value
        key_file.parent.mkdir(parents=True, exist_ok=True)
        value = secrets.token_hex(32)
        key_file.write_text(value, encoding="utf-8")
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass
        return value
    except OSError:
        return secrets.token_hex(32)


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
