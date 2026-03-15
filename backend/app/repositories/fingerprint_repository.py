from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from app.core.paths import tenant_path
from app.models.audio_fingerprint import AudioFingerprint

if os.name == "nt":  # pragma: no cover
    import msvcrt
else:  # pragma: no cover
    import fcntl

_THREAD_LOCK = threading.Lock()


def _fingerprints_file(tenant_id: str) -> Path:
    return tenant_path(tenant_id, "catalog", "audio_fingerprints.json")


def _lock_file(tenant_id: str) -> Path:
    return tenant_path(tenant_id, "catalog", "audio_fingerprints.lock")


@contextmanager
def _file_lock(lock_path: Path, timeout_seconds: float = 5.0):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+b") as handle:
        start = time.time()
        while True:
            try:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() - start > timeout_seconds:
                    raise TimeoutError("Timeout acquiring fingerprint repository lock")
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


def _load(tenant_id: str) -> list[dict]:
    path = _fingerprints_file(tenant_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tenant_id: str, payload: list[dict]) -> None:
    path = _fingerprints_file(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_all_fingerprints(tenant_id: str = "default") -> list[AudioFingerprint]:
    with _THREAD_LOCK:
        with _file_lock(_lock_file(tenant_id)):
            return [AudioFingerprint.model_validate(item) for item in _load(tenant_id)]


def save_fingerprint(record: AudioFingerprint, tenant_id: str = "default") -> AudioFingerprint:
    with _THREAD_LOCK:
        with _file_lock(_lock_file(tenant_id)):
            items = _load(tenant_id)
            existing_idx = next(
                (
                    idx
                    for idx, item in enumerate(items)
                    if item.get("source_type") == record.source_type and item.get("source_id") == record.source_id
                ),
                None,
            )
            data = record.model_dump(mode="json")
            if existing_idx is not None:
                items[existing_idx] = data
            else:
                items.append(data)
            _save(tenant_id, items)
    return record
