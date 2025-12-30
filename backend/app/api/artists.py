from fastapi import APIRouter
from app.schemas.artist import ArtistCreate, ArtistResponse
from app.models.artist import Artist
from typing import List

router = APIRouter(prefix="/artists", tags=["Artists"])

ARTISTS_DB = []

@router.post("", response_model=ArtistResponse)
def create_artist(payload: ArtistCreate):
    artist = Artist(
        name=payload.name,
        type=payload.type
    )
    ARTISTS_DB.append(artist)
    return artist

@router.get("", response_model=List[ArtistResponse])
def list_artists():
    return ARTISTS_DB