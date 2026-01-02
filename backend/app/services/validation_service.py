from typing import List, Dict, Any
from app.ddex.ern_builder import build_ern
from app.services.workbench_client import validate_ern, normalize_validation_result

class ValidationResult:
    def __init__(self, code: str, level: str, message: str, field: str = None, step: str = None):
        self.code = code
        self.level = level  # ERROR, WARNING, INFO
        self.message = message
        self.field = field
        self.step = step

def validate_release_draft(release_draft) -> List[ValidationResult]:
    errors = []

    # Artist validation
    if not release_draft.artist:
        errors.append(ValidationResult(
            "ARTIST_MISSING", "ERROR", "Artista es obligatorio", "artist", "artist"
        ))
    else:
        artist = release_draft.artist
        if not artist.get("display_name"):
            errors.append(ValidationResult(
                "ARTIST_NAME_REQUIRED", "ERROR", "Nombre del artista es obligatorio", "artist.display_name", "artist"
            ))
        if not artist.get("country"):
            errors.append(ValidationResult(
                "ARTIST_COUNTRY_REQUIRED", "ERROR", "País del artista es obligatorio", "artist.country", "artist"
            ))

    # Release validation
    if not release_draft.release:
        errors.append(ValidationResult(
            "RELEASE_MISSING", "ERROR", "Información del release es obligatoria", "release", "release"
        ))
    else:
        release = release_draft.release
        if not release.get("title", {}).get("text"):
            errors.append(ValidationResult(
                "RELEASE_TITLE_MISSING", "ERROR", "Título del release es obligatorio", "release.title.text", "release"
            ))
        if not release.get("title", {}).get("language"):
            errors.append(ValidationResult(
                "RELEASE_LANGUAGE_MISSING", "ERROR", "Idioma del título es obligatorio", "release.title.language", "release"
            ))

    # Tracks validation
    if not release_draft.tracks:
        errors.append(ValidationResult(
            "TRACKS_MISSING", "ERROR", "Al menos un track es obligatorio", "tracks", "tracks"
        ))
    else:
        for i, track in enumerate(release_draft.tracks):
            if not track.get("title", {}).get("text"):
                errors.append(ValidationResult(
                    "TRACK_TITLE_MISSING", "ERROR", f"Título del track {i+1} es obligatorio", f"tracks[{i}].title.text", "tracks"
                ))

    # Artwork validation
    if not release_draft.artwork:
        errors.append(ValidationResult(
            "ARTWORK_MISSING", "ERROR", "Artwork es obligatorio", "artwork", "artwork"
        ))

    # Deals validation
    if not release_draft.deals:
        errors.append(ValidationResult(
            "DEALS_MISSING", "ERROR", "Fechas y territorios son obligatorios", "deals", "deals"
        ))

    # Parties validation
    if not release_draft.artist or not release_draft.artist.get("display_name"):
        errors.append(ValidationResult(
            "MAIN_ARTIST_MISSING", "ERROR", "MainArtist es obligatorio", "artist", "artist"
        ))

    # RightsController is always present via config, but we can check if artist is set

    # Deals validation
    # For now, deals are auto-generated, so assume valid

    # Cover art validation
    if not release_draft.artwork:
        errors.append(ValidationResult(
            "ARTWORK_MISSING", "ERROR", "Cover art es obligatorio", "artwork", "artwork"
        ))

    return errors

def validate_release(draft):
    xml = build_ern(draft)
    result = validate_ern(xml)
    return normalize_validation_result(result)