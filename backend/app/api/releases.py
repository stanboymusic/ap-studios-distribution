from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas.release import ReleaseCreate, ReleaseResponse, ReleaseUpdate
from app.models.release import ReleaseDraft
from uuid import UUID, uuid4
from typing import List
from mutagen import File as MutagenFile
import shutil
import os

router = APIRouter(prefix="/releases", tags=["Releases"])

RELEASES_DB = []

@router.post("/", response_model=ReleaseResponse)
def create_release(data: ReleaseCreate):
    print("DEBUG: create_release called with data:", data.dict())
    release = ReleaseDraft()
    release.title = data.title
    release.release_type = data.release_type
    release.original_release_date = data.original_release_date
    release.language = data.language
    release.territories = data.territories

    RELEASES_DB.append(release)

    return ReleaseResponse(
        id=release.id,
        release_id=release.id,
        title=release.title,
        type=release.release_type.value,
        status=release.status
    )

@router.get("/", response_model=List[ReleaseResponse])
def list_releases():
    print("DEBUG: list_releases called, returning", len(RELEASES_DB), "releases")
    return RELEASES_DB

@router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(release_id: UUID):
    for release in RELEASES_DB:
        if release.id == release_id:
            return release
    raise HTTPException(status_code=404, detail="Release not found")

@router.put("/{release_id}", response_model=ReleaseResponse)
def update_release(release_id: UUID, payload: ReleaseUpdate):
    for release in RELEASES_DB:
        if release.id == release_id:
            if payload.upc:
                release.upc = payload.upc
            if payload.original_release_date:
                release.original_release_date = payload.original_release_date
            return release
    raise HTTPException(status_code=404, detail="Release not found")

@router.post("/{release_id}/audio")
def upload_audio(
    release_id: UUID,
    file: UploadFile = File(...),
    isrc: str = None
):
    # Buscar release
    for release in RELEASES_DB:
        if release.id == release_id:

            # Validar extensión
            if not file.filename.lower().endswith((".wav", ".flac")):
                raise HTTPException(
                    status_code=400,
                    detail="Only WAV or FLAC files are allowed"
                )

            # Guardar archivo
            file_path = f"storage/audio/{release.id}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Leer duración
            audio = MutagenFile(file_path)
            if audio is None or not audio.info:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to read audio file"
                )

            duration_seconds = int(audio.info.length)

            # Guardar metadata
            release.track_file = file_path
            release.isrc = isrc
            release.duration = duration_seconds

            return {
                "message": "Audio uploaded successfully",
                "duration": duration_seconds,
                "file": file.filename
            }

    raise HTTPException(status_code=404, detail="Release not found")