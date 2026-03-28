from __future__ import annotations

from app.ern.builder.serializers.releases import ERNBuildError

PLACEHOLDER_ISRC_PREFIXES = ("USABC", "XXXX", "US-ABC")


def validate_isrc_for_ern(isrc: str | None, track_title: str = "") -> str:
    if not isrc:
        raise ERNBuildError(
            f"Track '{track_title}' has no ISRC - assign one before delivery"
        )
    clean = isrc.replace("-", "").strip().upper()
    for prefix in PLACEHOLDER_ISRC_PREFIXES:
        if clean.startswith(prefix.replace("-", "")):
            raise ERNBuildError(
                f"Track '{track_title}' has placeholder ISRC '{isrc}'"
                " - assign a real ISRC before delivery"
            )
    if len(clean) != 12:
        raise ERNBuildError(
            f"ISRC '{isrc}' for track '{track_title}' is invalid"
            " - must be 12 characters"
        )
    return isrc
