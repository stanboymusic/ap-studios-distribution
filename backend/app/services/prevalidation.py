def validate_release(release: dict, tracks: list):
    errors = []

    if not release.get("title"):
        errors.append("Release title missing")

    if not tracks or len(tracks) == 0:
        errors.append("Release must contain at least one track")

    for track in tracks:
        if not track.get("duration_seconds"):
            errors.append(f"Track '{track['title']}' has no duration")

    return errors