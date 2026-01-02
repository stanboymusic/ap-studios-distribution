from fastapi import APIRouter, UploadFile, File, Form
from uuid import uuid4
from mutagen import File as MutagenFile
import io
import os
import shutil

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.post("/")
async def create_track(
    release_id: str = Form(...),
    title: str = Form(...),
    track_number: int = Form(...),
    explicit: bool = Form(False),
    audio: UploadFile = File(...)
):
    # Read audio bytes
    audio_bytes = await audio.read()

    # Extract duration using mutagen
    audio_stream = io.BytesIO(audio_bytes)
    audio_info = MutagenFile(audio_stream)

    duration = round(audio_info.info.length, 2) if audio_info and audio_info.info else None

    if duration is None:
        return {"error": "Unable to read audio file duration"}

    # Generate track_id
    track_id = f"TRK-{uuid4()}"

    # Save file to storage
    os.makedirs("storage/audio", exist_ok=True)
    file_path = f"storage/audio/{release_id}_{track_id}_{audio.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(audio_bytes)

    return {
        "track_id": track_id,
        "release_id": release_id,
        "title": title,
        "track_number": track_number,
        "duration_seconds": duration,
        "explicit": explicit,
        "file_path": file_path,
        "status": "ok"
    }