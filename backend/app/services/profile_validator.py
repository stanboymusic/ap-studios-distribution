from app.config.ddex import ERNProfile
from fastapi import HTTPException

def validate_profile(profile: ERNProfile, data):
    if profile == ERNProfile.AUDIO_ALBUM:
        if len(data.get("releases", {})) < 1:
            raise HTTPException(status_code=400, detail="AudioAlbum requires at least one release")
        if not data.get("deals"):
            raise HTTPException(status_code=400, detail="AudioAlbum requires deals")
    elif profile == ERNProfile.AUDIO_SINGLE:
        if len(data.get("releases", {})) != 1:
            raise HTTPException(status_code=400, detail="AudioSingle requires exactly one release")
        if not data.get("deals"):
            raise HTTPException(status_code=400, detail="AudioSingle requires deals")
    # Add more validations as needed