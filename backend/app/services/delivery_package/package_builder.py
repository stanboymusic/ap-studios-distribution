from __future__ import annotations

import zipfile
from pathlib import Path
from uuid import uuid4

from app.core.paths import tenant_path
from app.models.delivery_package import DeliveryPackageRecord
from app.repositories.delivery_repository import save_delivery_package
from app.services.delivery_package.asset_collector import collect_assets
from app.services.delivery_package.manifest_builder import build_checksums_lines, build_manifest


def build_delivery_package(release_id: str, tenant_id: str = "default") -> str:
    assets = collect_assets(release_id=release_id, tenant_id=tenant_id)
    manifest_xml = build_manifest(assets)
    checksum_lines = build_checksums_lines(assets)

    packages_dir = tenant_path(tenant_id, "packages")
    packages_dir.mkdir(parents=True, exist_ok=True)
    package_path = packages_dir / f"{release_id}.zip"

    tmp_dir = packages_dir / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    nonce = uuid4().hex
    temp_manifest = tmp_dir / f"{release_id}_{nonce}_manifest.xml"
    temp_checksums = tmp_dir / f"{release_id}_{nonce}_checksums.txt"
    temp_manifest.write_bytes(manifest_xml)
    temp_checksums.write_text("\n".join(checksum_lines), encoding="utf-8")
    try:
        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(assets["ern"], "ERN.xml")
            for audio in assets.get("audio", []):
                audio_path = Path(audio)
                archive.write(audio_path, f"audio/{audio_path.name}")
            artwork = assets.get("artwork")
            if artwork:
                artwork_path = Path(artwork)
                archive.write(artwork_path, f"artwork/{artwork_path.name}")
            archive.write(temp_manifest, "manifest.xml")
            archive.write(temp_checksums, "checksums.txt")
    finally:
        try:
            temp_manifest.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            temp_checksums.unlink(missing_ok=True)
        except Exception:
            pass

    record = DeliveryPackageRecord.create(
        release_id=release_id,
        tenant_id=tenant_id,
        file_path=str(package_path),
        status="PACKAGE_CREATED",
        manifest_path="manifest.xml",
    )
    save_delivery_package(record)

    return str(package_path)
