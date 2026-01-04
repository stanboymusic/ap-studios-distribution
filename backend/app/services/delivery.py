import os
from pathlib import Path
from app.services.ddex_packager import build_delivery_zip, Asset

def build_delivery_package(release_id: str, ern_xml: str, tracks: list, cover_path: str, artist_name: str):
    """
    Construye el paquete de entrega DDEX usando el packager oficial.

    Args:
        release_id: ID del release
        ern_xml: Contenido XML del ERN
        tracks: Lista de tracks con 'file_path', 'isrc', etc.
        cover_path: Ruta al archivo de cover
        artist_name: Nombre del artista (no usado en naming DDEX)

    Returns:
        Ruta al archivo ZIP creado
    """
    assets = []

    # Agregar tracks de audio
    for track in tracks:
        if 'file_path' in track and os.path.exists(track['file_path']):
            isrc = track.get('isrc', 'UNKNOWN')
            if isrc and isrc != 'UNKNOWN':
                relative_path = f"resources/audio/{isrc}.wav"
                assets.append(Asset(relative_path, Path(track['file_path'])))

    # Agregar artwork
    if cover_path and os.path.exists(cover_path):
        relative_path = "resources/images/cover.jpg"
        assets.append(Asset(relative_path, Path(cover_path)))

    # Construir ZIP usando el packager DDEX
    zip_path = build_delivery_zip(release_id, ern_xml, assets)

    return zip_path