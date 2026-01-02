import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

BASE_DELIVERY_PATH = "deliveries"

def sanitize_filename(name: str) -> str:
    """Sanitize filename for filesystem"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def build_delivery_package(release_id: str, ern_xml: str, tracks: list, cover_path: str, artist_name: str):
    # Create package name: APSTUDIOS_ERN_YYYYMMDD_XXXX
    timestamp = datetime.now().strftime("%Y%m%d")
    package_name = f"APSTUDIOS_ERN_{timestamp}_{release_id[:4].upper()}"
    base_path = Path(BASE_DELIVERY_PATH) / package_name

    # Create structure
    meta_path = base_path / "metadata"
    audio_path = base_path / "resources" / "audio"
    images_path = base_path / "resources" / "images"

    meta_path.mkdir(parents=True, exist_ok=True)
    audio_path.mkdir(parents=True, exist_ok=True)
    images_path.mkdir(parents=True, exist_ok=True)

    # Save ERN XML
    ern_file = meta_path / "release-notification.xml"
    ern_file.write_text(ern_xml, encoding="utf-8")

    # Copy audio files with proper naming
    for i, track in enumerate(tracks, 1):
        if 'file_path' in track and os.path.exists(track['file_path']):
            isrc = track.get('isrc', f'UNKNOWN{i:02d}')
            title = sanitize_filename(track.get('title', {}).get('text', f'Track{i}'))
            artist = sanitize_filename(artist_name)
            filename = f"{isrc}_{title}_{artist}.wav"
            shutil.copy(track['file_path'], audio_path / filename)

    # Copy artwork
    if cover_path and os.path.exists(cover_path):
        filename = "COVER_3000x3000.jpg"
        shutil.copy(cover_path, images_path / filename)

    # Create ZIP
    zip_path = Path(BASE_DELIVERY_PATH) / f"{package_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in base_path.rglob('*'):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(base_path))

    # Clean up temp directory
    shutil.rmtree(base_path)

    return str(zip_path)