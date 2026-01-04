from fastapi import APIRouter, UploadFile, File, Form
from uuid import uuid4
from mutagen import File as MutagenFile
import io
import os
import shutil
import wave
import struct

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
    release_id: str = Form(...),
    title: str = Form(...),
    track_number: int = Form(...),
    explicit: bool = Form(False),
    isrc: str = Form(None),
    audio: UploadFile = File(...)
):
    # Read audio bytes
    audio_bytes = await audio.read()

    # Generate track_id
    track_id = f"TRK-{uuid4()}"

    # Save file to storage first to help mutagen and ensure it's saved
    os.makedirs("storage/audio", exist_ok=True)
    file_path = f"storage/audio/{release_id}_{track_id}_{audio.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(audio_bytes)

    # Extract duration using mutagen from the saved file
    duration = None
    try:
        audio_info = MutagenFile(file_path)
        if audio_info and audio_info.info:
            duration = round(audio_info.info.length, 2)
    except Exception as e:
        print(f"DEBUG: Mutagen error: {e}")

    # Fallback for WAV files using wave module
    if duration is None and audio.filename.lower().endswith('.wav'):
        try:
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = round(frames / float(rate), 2)
        except Exception as e:
            print(f"DEBUG: Wave module error: {e}")
            # Final fallback: manual parsing
            duration = get_wav_duration_manual(file_path)

    if duration is None:
        # If mutagen fails, maybe it's a format it doesn't recognize or file is corrupted
        # For now, let's not block but maybe return a default or log it
        print(f"WARNING: Unable to read duration for {file_path}")
        duration = 0.0

    return {
        "track_id": track_id,
        "release_id": release_id,
        "title": title,
        "track_number": track_number,
        "duration_seconds": duration,
        "explicit": explicit,
        "isrc": isrc,
        "file_path": file_path,
        "status": "ok"
    }