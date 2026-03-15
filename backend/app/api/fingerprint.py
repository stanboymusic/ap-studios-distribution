from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.paths import storage_path
from app.fingerprinting.fingerprint_service import process_audio_fingerprint

router = APIRouter(prefix="/audio", tags=["Audio Fingerprint"])


@router.post("/fingerprint/{track_id}")
async def fingerprint_audio(track_id: str, request: Request, file: UploadFile = File(...)):
    tenant_id = request.state.tenant_id
    tmp_dir = storage_path("tmp", "fingerprints")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "").suffix or ".bin"
    tmp_path = tmp_dir / f"{uuid4()}{extension}"
    with open(tmp_path, "wb") as handle:
        handle.write(await file.read())

    try:
        result = process_audio_fingerprint(
            source_id=track_id,
            source_type="track",
            file_path=str(tmp_path),
            asset_path=str(tmp_path),
            tenant_id=tenant_id,
            ignore_same_source=True,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    if result["duplicate"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Duplicate audio detected",
                "duplicate_of": result["track_id"],
                "similarity": result["similarity"],
                "source_type": result["source_type"],
            },
        )
    return result
