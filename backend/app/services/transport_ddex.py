from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime
from typing import Any, Dict

from app.services.sftp_connector import SFTPConnector


def _sha256_path(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_delivery_manifest(local_path: str, remote_path: str) -> Dict[str, Any]:
    return {
        "file_name": os.path.basename(local_path),
        "local_path": local_path,
        "remote_path": remote_path,
        "size_bytes": os.path.getsize(local_path),
        "sha256": _sha256_path(local_path),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def upload_with_retry(
    connector: SFTPConnector,
    local_path: str,
    remote_path: str,
    retries: int = 3,
    connect_timeout_seconds: float = 3.0,
    retry_backoff_seconds: float = 1.5,
) -> Dict[str, Any]:
    manifest = build_delivery_manifest(local_path=local_path, remote_path=remote_path)
    last_error: str | None = None

    for attempt in range(1, retries + 1):
        try:
            connector.connect(timeout_seconds=connect_timeout_seconds)
            connector.upload(local_path, remote_path)
            connector.disconnect()
            manifest["attempt"] = attempt
            manifest["status"] = "uploaded"
            return manifest
        except Exception as exc:
            last_error = str(exc)
            try:
                connector.disconnect()
            except Exception:
                pass
            if attempt < retries:
                time.sleep(retry_backoff_seconds * attempt)

    raise RuntimeError(f"SFTP upload failed after {retries} attempts: {last_error}")
