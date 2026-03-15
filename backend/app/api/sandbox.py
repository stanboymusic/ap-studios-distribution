from __future__ import annotations

import json
import zipfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.paths import SANDBOX_DSP_DIR, sandbox_dsp_path
from app.services.delivery_logger import log_event


router = APIRouter(prefix="/sandbox", tags=["Sandbox DSP"])


class ModerationRequest(BaseModel):
    reason: str = ""
    issues: List[str] = []


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _dir_mtime(path: Path) -> str:
    try:
        return datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() + "Z"
    except Exception:
        return datetime.utcnow().isoformat() + "Z"


def _summarize_release_dir(base: Path, release_id: str) -> Dict[str, Any]:
    d = base / release_id
    status_path = d / "status.json"
    status = _read_json(status_path) if status_path.exists() else None
    has_ern = any(p.name.lower().endswith(".xml") for p in d.glob("*.xml"))
    has_assets = (d / "resources").exists()
    return {
        "release_id": release_id,
        "path": str(d),
        "updated_at": _dir_mtime(d),
        "status": status,
        "has_ern": has_ern,
        "has_assets": has_assets,
    }


@router.get("/overview")
def sandbox_overview():
    """
    Monitor del DSP sandbox:
    - incoming: ZIPs en cola
    - processing: entregas en proceso (dir por release)
    - accepted/rejected: resultados con status.json
    """
    root = SANDBOX_DSP_DIR
    incoming = sandbox_dsp_path("incoming")
    processing = sandbox_dsp_path("processing")
    accepted = sandbox_dsp_path("accepted")
    rejected = sandbox_dsp_path("rejected")
    logs = sandbox_dsp_path("logs")

    for d in [incoming, processing, accepted, rejected, logs]:
        d.mkdir(parents=True, exist_ok=True)

    incoming_items = []
    for z in sorted(incoming.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        rid = z.stem.replace("delivery_", "")
        incoming_items.append({
            "release_id": rid,
            "file": z.name,
            "path": str(z),
            "updated_at": _dir_mtime(z),
            "size": z.stat().st_size,
        })

    processing_items = []
    for d in sorted([p for p in processing.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True):
        processing_items.append({
            "release_id": d.name,
            "path": str(d),
            "updated_at": _dir_mtime(d),
        })

    accepted_items = []
    for d in sorted([p for p in accepted.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True):
        accepted_items.append(_summarize_release_dir(accepted, d.name))

    rejected_items = []
    for d in sorted([p for p in rejected.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True):
        rejected_items.append(_summarize_release_dir(rejected, d.name))

    return {
        "root": str(root),
        "incoming": incoming_items,
        "processing": processing_items,
        "accepted": accepted_items,
        "rejected": rejected_items,
    }


@router.get("/delivery/{release_id}")
def sandbox_delivery_detail(release_id: str):
    """Detalle de una entrega dentro del sandbox (accepted/rejected/processing)."""
    rid = (release_id or "").strip()
    try:
        UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id")

    for bucket in ["accepted", "rejected", "processing"]:
        d = sandbox_dsp_path(bucket, rid)
        if d.exists() and d.is_dir():
            status = _read_json(d / "status.json")
            files = []
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    rel = str(p.relative_to(d)).replace("\\", "/")
                    files.append({"path": rel, "size": p.stat().st_size})
            return {"bucket": bucket, "release_id": rid, "path": str(d), "status": status, "files": files}

    incoming_zip = sandbox_dsp_path("incoming", f"delivery_{rid}.zip")
    if incoming_zip.exists():
        return {"bucket": "incoming", "release_id": rid, "path": str(incoming_zip), "status": None, "files": []}

    raise HTTPException(status_code=404, detail="Delivery not found in sandbox")


def _manual_decision(release_id: str, decision: str, reason: str, issues: List[str]):
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id")

    incoming_zip = sandbox_dsp_path("incoming", f"delivery_{rid}.zip")
    processing_dir = sandbox_dsp_path("processing", rid)
    target_bucket = "accepted" if decision == "ACCEPTED" else "rejected"
    target_dir = sandbox_dsp_path(target_bucket, rid)
    target_dir.mkdir(parents=True, exist_ok=True)

    # If a processing dir exists, move everything to target.
    if processing_dir.exists() and processing_dir.is_dir():
        for item in processing_dir.iterdir():
            shutil.move(str(item), str(target_dir / item.name))
        try:
            processing_dir.rmdir()
        except Exception:
            pass
    elif incoming_zip.exists():
        # Move zip and extract so the payload is visible in UI
        moved_zip = target_dir / incoming_zip.name
        shutil.move(str(incoming_zip), str(moved_zip))
        try:
            with zipfile.ZipFile(moved_zip, "r") as z:
                z.extractall(target_dir)
        except Exception:
            pass
    else:
        # Nothing to decide on
        raise HTTPException(status_code=404, detail="No incoming zip or processing dir for this release")

    status_data = {
        "release_id": rid,
        "status": decision,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "issues": issues,
        "manual": True,
        "reason": reason,
    }
    (target_dir / "status.json").write_text(json.dumps(status_data, indent=2), encoding="utf-8")

    # Log to backend delivery timeline as DSP SANDBOX
    try:
        log_event(
            release_id=release_uuid,
            dsp="DSP SANDBOX",
            event_type=decision,
            message=f"Manual {decision.lower()}: {reason}" if reason else f"Manual {decision.lower()}",
        )
    except Exception:
        pass

    return {"status": decision, "path": str(target_dir), "status_json": status_data}


@router.post("/approve/{release_id}")
def sandbox_approve(release_id: str, payload: ModerationRequest):
    return _manual_decision(release_id, "ACCEPTED", payload.reason, payload.issues)


@router.post("/reject/{release_id}")
def sandbox_reject(release_id: str, payload: ModerationRequest):
    issues = payload.issues or []
    if payload.reason:
        issues = [payload.reason, *issues]
    return _manual_decision(release_id, "REJECTED", payload.reason, issues)
