from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from uuid import UUID, uuid4
from mutagen import File as MutagenFile
import struct
from datetime import datetime
from app.core.paths import storage_path
from app.catalog.catalog_service import create_track as create_catalog_track
from app.fingerprinting.fingerprint_service import process_audio_fingerprint
from app.services.catalog_service import CatalogService
from app.core.auth import ensure_release_access

router = APIRouter(prefix="/tracks", tags=["Tracks"])


def get_wav_duration_manual(file_path):
    """Fallback manual parser for WAV files, including IEEE Float (Format 3)."""
    try:
        with open(file_path, 'rb') as f:
            # RIFF Header
            riff = f.read(12)
            if len(riff) < 12 or riff[0:4] != b'RIFF' or riff[8:12] != b'WAVE':
                return None
            
            byte_rate = None
            data_size = 0
            
            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                
                chunk_id, chunk_size = struct.unpack('<4sI', header)
                
                if chunk_id == b'fmt ':
                    fmt_data = f.read(chunk_size)
                    if len(fmt_data) >= 12:
                        # audio_format(2), num_channels(2), sample_rate(4), byte_rate(4)
                        _, _, _, b_rate = struct.unpack('<HHII', fmt_data[:12])
                        byte_rate = b_rate
                    if chunk_size % 2: f.read(1) # skip padding
                elif chunk_id == b'data':
                    data_size = chunk_size
                    f.seek(chunk_size, 1)
                    if chunk_size % 2: f.read(1) # skip padding
                else:
                    # Skip other chunks
                    actual_size = chunk_size + (chunk_size % 2)
                    f.seek(actual_size, 1)
            
            if byte_rate and data_size:
                return round(data_size / byte_rate, 2)
    except Exception as e:
        print(f"DEBUG: Manual WAV parser error: {e}")
    return None

@router.post("/")
async def create_track(
    request: Request,
    release_id: str = Form(...),
    title: str = Form(...),
    track_number: int = Form(...),
    explicit: bool = Form(False),
    isrc: str = Form(None),
    audio: UploadFile = File(...)
):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    ensure_release_access(request, release)

    try:
        track_identity = create_catalog_track(
            title=title,
            artist_id=str(release.artist_id) if getattr(release, "artist_id", None) else "",
            tenant_id=tenant_id,
            isrc=isrc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resolved_isrc = track_identity["isrc"]

    # Read audio bytes
    audio_bytes = await audio.read()

    # Generate track_id
    track_uuid = uuid4()
    track_id = f"TRK-{track_uuid}"

    # Save file to storage
    directory = storage_path("audio")
    directory.mkdir(parents=True, exist_ok=True)
    extension = audio.filename.split('.')[-1] if '.' in audio.filename else 'wav'
    file_path = directory / f"{track_uuid}.{extension}"
    with open(file_path, "wb") as buffer:
        buffer.write(audio_bytes)

    # Extract duration
    duration = None
    try:
        audio_info = MutagenFile(str(file_path))
        if audio_info and audio_info.info:
            duration = round(audio_info.info.length, 2)
    except Exception as e:
        print(f"DEBUG: Mutagen error: {e}")

    if duration is None and audio.filename.lower().endswith('.wav'):
        duration = get_wav_duration_manual(str(file_path))

    if duration is None:
        duration = 0.0

    try:
        fingerprint_result = process_audio_fingerprint(
            source_id=str(track_uuid),
            source_type="track",
            file_path=str(file_path),
            asset_path=str(file_path),
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if fingerprint_result["duplicate"]:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Duplicate audio detected",
                "duplicate_of": fingerprint_result["track_id"],
                "similarity": fingerprint_result["similarity"],
                "source_type": fingerprint_result["source_type"],
            },
        )

    # Save asset metadata
    asset_data = {
        "id": str(track_uuid),
        "type": "audio",
        "path": str(file_path),
        "duration": duration,
        "title": title,
        "isrc": resolved_isrc,
        "fingerprint": {
            "id": fingerprint_result["fingerprint_id"],
            "hash": fingerprint_result["fingerprint"],
        },
        "created_at": datetime.utcnow().isoformat()
    }
    CatalogService.save_asset(asset_data, tenant_id=tenant_id)
    
    # Update release in catalog
    track_entry = {
        "track_id": track_id,
        "title": title,
        "track_number": track_number,
        "duration_seconds": duration,
        "explicit": explicit,
        "isrc": resolved_isrc,
        "file_path": str(file_path),
        "fingerprint": {
            "id": fingerprint_result["fingerprint_id"],
            "hash": fingerprint_result["fingerprint"],
        },
    }
    if not hasattr(release, "tracks"):
        release.tracks = []
    release.tracks.append(track_entry)
    
    if not hasattr(release, "track_ids"):
        release.track_ids = []
    release.track_ids.append(track_uuid)
    
    CatalogService.save_release(release, tenant_id=tenant_id)

    return {
        "track_id": track_id,
        "release_id": release_id,
        "title": title,
        "track_number": track_number,
        "duration_seconds": duration,
        "explicit": explicit,
        "isrc": resolved_isrc,
        "fingerprint": {
            "id": fingerprint_result["fingerprint_id"],
            "hash": fingerprint_result["fingerprint"],
        },
        "file_path": str(file_path),
        "status": "ok"
    }
