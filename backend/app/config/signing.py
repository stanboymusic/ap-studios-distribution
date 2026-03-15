from __future__ import annotations

import os
from pathlib import Path

from app.core.paths import BACKEND_DIR


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ERN_SIGNING_ENABLED = _as_bool(os.getenv("ERN_SIGNING_ENABLED"), default=False)
ERN_SIGNING_REQUIRE_CERT = _as_bool(os.getenv("ERN_SIGNING_REQUIRE_CERT"), default=True)

DEFAULT_KEY_PATH = BACKEND_DIR / "certs" / "key.pem"
DEFAULT_CERT_PATH = BACKEND_DIR / "certs" / "cert.pem"

# Docker secrets-compatible fallback paths.
SECRET_KEY_PATH = Path("/run/secrets/ddex_private_key")
SECRET_CERT_PATH = Path("/run/secrets/ddex_public_cert")

_key_env = os.getenv("ERN_SIGNING_KEY_PATH")
_cert_env = os.getenv("ERN_SIGNING_CERT_PATH")

ERN_SIGNING_KEY_PATH = Path(_key_env) if _key_env else (SECRET_KEY_PATH if SECRET_KEY_PATH.exists() else DEFAULT_KEY_PATH)
ERN_SIGNING_CERT_PATH = Path(_cert_env) if _cert_env else (SECRET_CERT_PATH if SECRET_CERT_PATH.exists() else DEFAULT_CERT_PATH)
