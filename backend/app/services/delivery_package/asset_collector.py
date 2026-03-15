from __future__ import annotations

from pathlib import Path

from app.core.paths import tenant_path


def collect_assets(release_id: str, tenant_id: str = "default") -> dict:
    base = tenant_path(tenant_id, "releases", release_id)
    if not base.exists():
        raise FileNotFoundError(f"Release staging directory not found: {base}")

    audio_dir = base / "audio"
    audio_files = sorted(
        [p for p in audio_dir.glob("*") if p.is_file()],
        key=lambda p: p.name.lower(),
    ) if audio_dir.exists() else []

    artwork = base / "cover.jpg"
    if not artwork.exists():
        fallback_images = []
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            fallback_images.extend([p for p in base.glob(pattern) if p.is_file()])
        artwork = fallback_images[0] if fallback_images else None

    ern_file = base / "ern_signed.xml"
    if not ern_file.exists():
        fallback = base / "ern.xml"
        if fallback.exists():
            ern_file = fallback

    if not ern_file.exists():
        raise FileNotFoundError(f"Signed ERN file not found for release {release_id} in {base}")
    if not audio_files:
        raise FileNotFoundError(f"No audio assets found in {audio_dir}")

    return {
        "base_dir": base,
        "audio": audio_files,
        "artwork": artwork,
        "ern": ern_file,
    }
