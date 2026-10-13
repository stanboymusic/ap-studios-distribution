"""
Persistencia segura en archivos JSON.

Problemas que resuelve (el catálogo vive en JSON, no en Postgres):
  1. Escritura atómica: se escribe a un temporal, fsync y os.replace. Si el
     proceso muere a mitad, el archivo original queda intacto.
  2. Bloqueo entre hilos Y procesos (uvicorn + celery worker), compatible con
     Windows (msvcrt) y Linux (fcntl), para que dos escrituras simultáneas no
     se pisen (lectura-modificación-escritura).
  3. Nunca "borrar todo en silencio": si el JSON está corrupto se guarda una
     copia de cuarentena, se intenta recuperar el .bak y, si no hay, se lanza
     un error en vez de devolver [] (que luego sobrescribiría todo).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

if os.name == "nt":  # pragma: no cover
    import msvcrt
else:  # pragma: no cover
    import fcntl

logger = logging.getLogger(__name__)
T = TypeVar("T")

_THREAD_LOCKS: dict[str, threading.Lock] = {}
_GUARD = threading.Lock()
_held = threading.local()


class StorageCorruptionError(RuntimeError):
    """El archivo JSON está corrupto y no hay copia de respaldo válida."""


def _thread_lock(key: str) -> threading.Lock:
    with _GUARD:
        lock = _THREAD_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _THREAD_LOCKS[key] = lock
        return lock


@contextmanager
def file_lock(path: Path, timeout: float = 15.0) -> Iterator[None]:
    """Lock exclusivo (re-entrante dentro del mismo hilo) para `path`."""
    path = Path(path)
    key = str(path.resolve())
    held: set[str] = getattr(_held, "keys", None) or set()
    _held.keys = held
    if key in held:  # ya lo tengo en este hilo -> no bloquear de nuevo
        yield
        return

    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    tlock = _thread_lock(key)
    if not tlock.acquire(timeout=timeout):
        raise TimeoutError(f"Timeout acquiring lock for {path.name}")
    try:
        with open(lock_path, "a+b") as handle:
            start = time.time()
            while True:
                try:
                    if os.name == "nt":  # pragma: no cover
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.time() - start > timeout:
                        raise TimeoutError(f"Timeout acquiring file lock for {path.name}")
                    time.sleep(0.03)
            held.add(key)
            try:
                yield
            finally:
                held.discard(key)
                try:
                    if os.name == "nt":  # pragma: no cover
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
    finally:
        tlock.release()


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        if path.exists():
            try:  # copia del último estado bueno
                shutil.copy2(path, path.with_name(path.name + ".bak"))
            except OSError:
                pass
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, data: Any, *, default: Callable[[Any], Any] | None = None, indent: int = 2) -> None:
    atomic_write_text(path, json.dumps(data, indent=indent, ensure_ascii=False, default=default))


def read_json(path: Path, default_factory: Callable[[], T] = list) -> T:  # type: ignore[assignment]
    """Lee JSON. Si no existe devuelve default. Si está corrupto: cuarentena + .bak, o error."""
    path = Path(path)
    if not path.exists():
        return default_factory()
    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return default_factory()
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        quarantine = path.with_name(f"{path.name}.corrupt-{stamp}")
        try:
            shutil.copy2(path, quarantine)
        except OSError:
            pass
        logger.error("JSON corrupto en %s (copia en %s): %s", path, quarantine, exc)
        bak = path.with_name(path.name + ".bak")
        if bak.exists():
            try:
                recovered = json.loads(bak.read_text(encoding="utf-8"))
                atomic_write_text(path, bak.read_text(encoding="utf-8"))
                logger.warning("Recuperado %s desde .bak", path)
                return recovered
            except Exception:
                pass
        raise StorageCorruptionError(f"Corrupted storage file: {path.name}") from exc


def update_json(
    path: Path,
    mutator: Callable[[Any], T],
    *,
    default_factory: Callable[[], Any] = list,
    default: Callable[[Any], Any] | None = None,
) -> T:
    """Lectura-modificación-escritura atómica y serializada. `mutator` modifica in-place."""
    with file_lock(path):
        data = read_json(path, default_factory)
        result = mutator(data)
        atomic_write_json(path, data, default=default)
        return result
