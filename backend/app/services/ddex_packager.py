import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import os
from app.core.paths import storage_path

def sha256(file_path: Path) -> str:
    """Calcula el hash SHA256 de un archivo."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

class Asset:
    def __init__(self, relative_path: str, file_path: Path):
        self.relative_path = relative_path
        self.file_path = file_path

def build_delivery_zip(release_id: str, ern_xml_content: str, assets: List[Asset]) -> str:
    """
    Construye el ZIP de entrega DDEX.

    Args:
        release_id: ID del release
        ern_xml_content: Contenido del XML ERN
        assets: Lista de assets con relative_path y file_path

    Returns:
        Ruta al archivo ZIP creado
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir) / f"delivery_{release_id}"
        resources_dir = base / "resources"
        audio_dir = resources_dir / "audio"
        image_dir = resources_dir / "images"

        audio_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)

        checksums = []

        for asset in assets:
            target = base / asset.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            # Copiar el archivo
            with open(asset.file_path, "rb") as src, open(target, "wb") as dst:
                dst.write(src.read())
            # Calcular checksum
            checksums.append(f"{asset.relative_path} SHA256 {sha256(target)}")

        # Escribir ERN en la raíz
        ern_path = base / "ern.xml"
        ern_path.write_text(ern_xml_content)

        # Escribir checksums
        checksums_path = base / "checksums.txt"
        checksums_path.write_text("\n".join(checksums))

        # Crear ZIP en la carpeta de deliveries
        delivery_dir = storage_path("deliveries")
        delivery_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = delivery_dir / f"delivery_{release_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for file in base.rglob("*"):
                if file.is_file():
                    z.write(file, file.relative_to(base))

        return str(zip_path)
