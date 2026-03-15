from fastapi import APIRouter, Request
from app.schemas.artist import ArtistCreate, ArtistResponse
from app.models.artist import Artist
from app.services.catalog_service import CatalogService
from typing import List

router = APIRouter(prefix="/artists", tags=["Artists"])

@router.post("/", response_model=ArtistResponse)
def create_artist(payload: ArtistCreate, request: Request):
    tenant_id = request.state.tenant_id
    existing = CatalogService.find_artist_by_name(payload.name, payload.type, tenant_id=tenant_id)
    if existing:
        return existing
    artist = Artist(
        name=payload.name,
        type=payload.type
    )
    CatalogService.save_artist(artist, tenant_id=tenant_id)
    return artist

@router.get("/", response_model=List[ArtistResponse])
def list_artists(request: Request):
    tenant_id = request.state.tenant_id
    return [a.to_dict() for a in CatalogService.get_artists(tenant_id=tenant_id)]
