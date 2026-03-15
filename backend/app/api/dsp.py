from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.paths import sandbox_dsp_path
from app.core.auth import require_admin
from app.services.dsp_monitor import scan_dsp, read_logs
from app.services.delivery_logger import log_event


router = APIRouter(prefix="/dsp", tags=["DSP Monitor"], dependencies=[Depends(require_admin)])


class RejectRequest(BaseModel):
    reason: str = ""


@router.get("/monitor")
def dsp_monitor():
    return scan_dsp()


@router.get("/logs/{release_id}")
def dsp_logs(release_id: str):
    return {"log": read_logs(release_id)}


def _append_log(release_id: str, line: str):
    logs_dir = sandbox_dsp_path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / f"release-{release_id}.log"
    ts = datetime.utcnow().isoformat() + "Z"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")


def _ensure_processing_payload(release_id: str) -> Path:
    """
    Ensures there is a directory under processing that contains extracted payload.
    Accepts either:
    - processing/<uuid>/ (existing)
    - processing/release-<uuid>/ (existing)
    - incoming/delivery_<uuid>.zip
    - incoming/release-<uuid>.zip
    """
    proc1 = sandbox_dsp_path("processing", release_id)
    proc2 = sandbox_dsp_path("processing", f"release-{release_id}")
    if proc1.exists() and proc1.is_dir():
        return proc1
    if proc2.exists() and proc2.is_dir():
        return proc2

    incoming1 = sandbox_dsp_path("incoming", f"delivery_{release_id}.zip")
    incoming2 = sandbox_dsp_path("incoming", f"release-{release_id}.zip")
    incoming = incoming1 if incoming1.exists() else incoming2
    if not incoming.exists():
        raise HTTPException(status_code=404, detail="No incoming zip or processing directory for this release")

    target = proc1
    target.mkdir(parents=True, exist_ok=True)
    moved_zip = target / incoming.name
    shutil.move(str(incoming), str(moved_zip))
    try:
        with zipfile.ZipFile(moved_zip, "r") as z:
            z.extractall(target)
    except Exception:
        pass
    return target


def _move_processing_to(release_id: str, dst_bucket: str) -> Path:
    src = _ensure_processing_payload(release_id)
    dst1 = sandbox_dsp_path(dst_bucket, release_id)
    dst2 = sandbox_dsp_path(dst_bucket, f"release-{release_id}")
    dst = dst1
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        shutil.move(str(item), str(dst / item.name))

    try:
        src.rmdir()
    except Exception:
        pass

    # status.json (DSP-like)
    status_data = {
        "release_id": release_id,
        "status": dst_bucket.upper(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "issues": [],
        "manual": True,
    }
    (dst / "status.json").write_text(json.dumps(status_data, indent=2), encoding="utf-8")
    return dst


@router.post("/approve/{release_id}")
def approve_release(release_id: str):
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id")

    dst = _move_processing_to(rid, "accepted")
    _append_log(rid, "APPROVED (manual)")

    # Connect with timeline
    try:
        log_event(release_id=release_uuid, dsp="DSP SANDBOX", event_type="ACCEPTED", message="Manual approved in monitor")
    except Exception:
        pass

    return {"status": "accepted", "path": str(dst)}


@router.post("/reject/{release_id}")
def reject_release(release_id: str, payload: RejectRequest):
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id")

    dst = _move_processing_to(rid, "rejected")
    _append_log(rid, f"REJECTED (manual): {payload.reason}".strip())

    # update status.json issues
    status_path = Path(dst) / "status.json"
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
        if payload.reason:
            data["issues"] = [payload.reason]
        status_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

    try:
        log_event(release_id=release_uuid, dsp="DSP SANDBOX", event_type="REJECTED", message=f"Manual rejected in monitor: {payload.reason}")
    except Exception:
        pass

    return {"status": "rejected", "path": str(dst)}
