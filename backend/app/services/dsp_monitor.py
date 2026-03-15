from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.paths import SANDBOX_DSP_DIR, sandbox_dsp_path


DSP_STATUSES = ["incoming", "processing", "accepted", "rejected"]


def _parse_release_id(name: str) -> Optional[str]:
    """
    Supports both formats:
    - release-<uuid>.zip / release-<uuid>/
    - delivery_<uuid>.zip / <uuid>/
    """
    n = name
    if n.startswith("release-"):
        n = n[len("release-") :]
    if n.startswith("delivery_"):
        n = n[len("delivery_") :]
    if n.lower().endswith(".zip"):
        n = n[:-4]
    return n or None


def _release_log_paths(release_id: str) -> List[Path]:
    logs_dir = sandbox_dsp_path("logs")
    return [
        logs_dir / f"release-{release_id}.log",
        logs_dir / f"{release_id}.log",
    ]


def _has_log(release_id: str) -> bool:
    return any(p.exists() for p in _release_log_paths(release_id))


def scan_dsp() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    base = SANDBOX_DSP_DIR
    for status in DSP_STATUSES:
        folder = base / status
        if not folder.exists():
            continue

        if status == "incoming":
            for item in folder.glob("*.zip"):
                rid = _parse_release_id(item.name)
                if not rid:
                    continue
                items.append({
                    "release_id": rid,
                    "status": status,
                    "path": str(item),
                    "has_log": _has_log(rid),
                })
        else:
            for item in folder.iterdir():
                if not item.is_dir():
                    continue
                rid = _parse_release_id(item.name)
                if not rid:
                    continue
                items.append({
                    "release_id": rid,
                    "status": status,
                    "path": str(item),
                    "has_log": _has_log(rid),
                })

    return items


def read_logs(release_id: str) -> str:
    for p in _release_log_paths(release_id):
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
    return ""

