from fastapi import APIRouter, HTTPException
from app.schemas.release import (
    ReleaseCreate,
    ReleaseUpdate,
    ReleaseResponse
)
from app.models.release import Release
from uuid import UUID
from typing import List

router = APIRouter(prefix="/releases", tags=["Releases"])

RELEASES_DB = []

@router.post("", response_model=ReleaseResponse)
def create_release(payload: ReleaseCreate):
    release = Release(
        title=payload.title,
        artist_id=payload.artist_id
    )
    RELEASES_DB.append(release)
    return release

@router.get("", response_model=List[ReleaseResponse])
def list_releases():
    return RELEASES_DB

@router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(release_id: UUID):
    for release in RELEASES_DB:
        if release.id == release_id:
            return release
    raise HTTPException(status_code=404, detail="Release not found")

@router.put("/{release_id}", response_model=ReleaseResponse)
def update_release(release_id: UUID, payload: ReleaseUpdate):
    for release in RELEASES_DB:
        if release.id == release_id:
            if payload.upc:
                release.upc = payload.upc
            if payload.original_release_date:
                release.original_release_date = payload.original_release_date
            return release
    raise HTTPException(status_code=404, detail="Release not found")