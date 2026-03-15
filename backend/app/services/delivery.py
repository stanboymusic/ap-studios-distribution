from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.core.paths import tenant_path
from app.services.delivery_package.package_builder import (
    build_delivery_package as build_packaged_delivery_zip,
)


def _copy_file(src: str | Path, dst: Path) -> bool:
    source = Path(src)
    if not source.exists() or not source.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dst)
    return True


def _track_target_name(track: dict[str, Any], source_path: Path, index: int) -> str:
    isrc = (track.get("isrc") or "").strip()
    track_id = (track.get("track_id") or f"track-{index+1}").strip()
    base = isrc or track_id
    ext = source_path.suffix or ".wav"
    return f"{base}{ext.lower()}"


def _stage_release_assets(
    release_id: str,
    ern_xml: str | bytes,
    tracks: list[dict[str, Any]],
    cover_path: str,
    tenant_id: str = "default",
) -> Path:
    release_dir = tenant_path(tenant_id, "releases", release_id)
    audio_dir = release_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    ern_path = release_dir / "ern_signed.xml"
    ern_text = ern_xml.decode("utf-8") if isinstance(ern_xml, bytes) else ern_xml
    ern_path.write_text(ern_text, encoding="utf-8")

    for index, track in enumerate(tracks or []):
        source_raw = track.get("file_path")
        if not source_raw:
            continue
        source = Path(source_raw)
        if not source.exists() or not source.is_file():
            continue
        target_name = _track_target_name(track, source, index)
        _copy_file(source, audio_dir / target_name)

    if cover_path:
        cover_src = Path(cover_path)
        if cover_src.exists() and cover_src.is_file():
            _copy_file(cover_src, release_dir / "cover.jpg")

    return release_dir


def build_delivery_package(
    release_id: str,
    ern_xml: str | bytes,
    tracks: list,
    cover_path: str,
    artist_name: str,
    tenant_id: str = "default",
) -> str:
    # Stage assets in a deterministic release folder first, then build manifest/checksums/zip.
    _stage_release_assets(
        release_id=release_id,
        ern_xml=ern_xml,
        tracks=tracks or [],
        cover_path=cover_path,
        tenant_id=tenant_id,
    )
    return build_packaged_delivery_zip(release_id=release_id, tenant_id=tenant_id)
