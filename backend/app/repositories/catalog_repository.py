from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from app.core.paths import storage_path, tenant_path
from app.models.identifiers import IdentifierState
from app.models.release import ReleaseDraft
from app.services.catalog_service import CatalogService

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None

if os.name == "nt":  # pragma: no cover
    import msvcrt
else:  # pragma: no cover
    import fcntl

T = TypeVar("T")
_THREAD_LOCK = threading.Lock()
IDENTIFIER_SCOPE = (os.getenv("IDENTIFIER_SCOPE") or "global").strip().lower()


def _redis_url() -> str | None:
    for key in ("IDENTIFIER_REDIS_URL", "CELERY_BROKER_URL", "REDIS_URL"):
        value = (os.getenv(key) or "").strip()
        if value.startswith("redis://"):
            return value
    return None


def _get_redis() -> Redis | None:
    if Redis is None:
        return None
    url = _redis_url()
    if not url:
        return None
    try:
        client = Redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def _scope_id(tenant_id: str) -> str:
    return "__global__" if IDENTIFIER_SCOPE == "global" else (tenant_id or "default")


def _state_file(tenant_id: str) -> Path:
    scope = _scope_id(tenant_id)
    if scope == "__global__":
        return storage_path("identifiers", "identifiers.json")
    return tenant_path(scope, "catalog", "identifiers.json")


def _lock_file(tenant_id: str) -> Path:
    scope = _scope_id(tenant_id)
    if scope == "__global__":
        return storage_path("identifiers", "identifiers.lock")
    return tenant_path(scope, "catalog", "identifiers.lock")


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
                    raise TimeoutError("Timeout acquiring identifier repository lock")
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


def _load_state(path: Path) -> IdentifierState:
    if not path.exists():
        return IdentifierState()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return IdentifierState(**payload)
    except Exception:
        return IdentifierState()


def _save_state(path: Path, state: IdentifierState) -> None:
    state.updated_at = datetime.utcnow()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def _mutate_state(tenant_id: str, fn: Callable[[IdentifierState], T]) -> T:
    state_path = _state_file(tenant_id)
    with _THREAD_LOCK:
        with _file_lock(_lock_file(tenant_id)):
            state = _load_state(state_path)
            result = fn(state)
            _save_state(state_path, state)
            return result


def get_next_isrc_sequence(tenant_id: str, year: str) -> int:
    scope = _scope_id(tenant_id)
    redis_client = _get_redis()
    if redis_client is not None:
        return int(redis_client.incr(f"ident:{scope}:isrc:seq:{year}"))

    def _next(state: IdentifierState) -> int:
        current = int(state.isrc_sequences.get(year, 0)) + 1
        state.isrc_sequences[year] = current
        return current

    return _mutate_state(scope, _next)


def get_next_upc_sequence(tenant_id: str, prefix: str) -> int:
    scope = _scope_id(tenant_id)
    redis_client = _get_redis()
    if redis_client is not None:
        return int(redis_client.incr(f"ident:{scope}:upc:seq:{prefix}"))

    def _next(state: IdentifierState) -> int:
        current = int(state.upc_sequences.get(prefix, 0)) + 1
        state.upc_sequences[prefix] = current
        return current

    return _mutate_state(scope, _next)


def reserve_isrc(tenant_id: str, isrc: str, source: str) -> bool:
    scope = _scope_id(tenant_id)
    value = (isrc or "").strip().upper()
    src = (source or "unknown").strip()

    redis_client = _get_redis()
    if redis_client is not None:
        key = f"ident:{scope}:isrc:reserved:{value}"
        return bool(redis_client.set(key, src, nx=True))

    def _reserve(state: IdentifierState) -> bool:
        if value in state.reserved_isrc:
            return False
        state.reserved_isrc[value] = {"source": src, "reserved_at": datetime.utcnow().isoformat() + "Z"}
        return True

    return _mutate_state(scope, _reserve)


def reserve_upc(tenant_id: str, upc: str, source: str) -> bool:
    scope = _scope_id(tenant_id)
    value = (upc or "").strip()
    src = (source or "unknown").strip()

    redis_client = _get_redis()
    if redis_client is not None:
        key = f"ident:{scope}:upc:reserved:{value}"
        return bool(redis_client.set(key, src, nx=True))

    def _reserve(state: IdentifierState) -> bool:
        if value in state.reserved_upc:
            return False
        state.reserved_upc[value] = {"source": src, "reserved_at": datetime.utcnow().isoformat() + "Z"}
        return True

    return _mutate_state(scope, _reserve)


def is_isrc_reserved(tenant_id: str, isrc: str) -> bool:
    scope = _scope_id(tenant_id)
    value = (isrc or "").strip().upper()
    redis_client = _get_redis()
    if redis_client is not None:
        return bool(redis_client.exists(f"ident:{scope}:isrc:reserved:{value}"))

    state = _load_state(_state_file(scope))
    return value in state.reserved_isrc


def is_upc_reserved(tenant_id: str, upc: str) -> bool:
    scope = _scope_id(tenant_id)
    value = (upc or "").strip()
    redis_client = _get_redis()
    if redis_client is not None:
        return bool(redis_client.exists(f"ident:{scope}:upc:reserved:{value}"))

    state = _load_state(_state_file(scope))
    return value in state.reserved_upc


def create_release(tenant_id: str, release: ReleaseDraft) -> ReleaseDraft:
    CatalogService.save_release(release, tenant_id=tenant_id)
    return release


def delete_release(tenant_id: str, release_id: str) -> bool:
    files = CatalogService._files(tenant_id)
    releases = CatalogService._load_json(files["releases"], tenant_id)
    before = len(releases)
    releases = [r for r in releases if str(r.get("id")) != str(release_id)]
    if len(releases) == before:
        return False
    CatalogService._save_json(files["releases"], releases, tenant_id)
    return True


def create_track(tenant_id: str, release_id: str, track_data: dict) -> dict:
    release = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if not release:
        raise ValueError("Release not found")
    if not hasattr(release, "tracks") or release.tracks is None:
        release.tracks = []
    release.tracks.append(track_data)
    CatalogService.save_release(release, tenant_id=tenant_id)
    return track_data


def is_upc_reserved(tenant_id: str, upc: str) -> bool:
    scope = _scope_id(tenant_id)
    value = (upc or "").strip()
    redis_client = _get_redis()
    if redis_client is not None:
        return bool(redis_client.exists(f"ident:{scope}:upc:reserved:{value}"))

    state = _load_state(_state_file(scope))
    return value in state.reserved_upc
