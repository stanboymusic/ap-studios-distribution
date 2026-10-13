from fastapi import APIRouter, Request
from app.schemas.artist import ArtistCreate, ArtistResponse
from app.models.artist import Artist
from app.services.catalog_service import CatalogService
from app.core.auth import (
    artist_accessible,
    current_user_id,
    ensure_authenticated,
    is_admin,
    user_release_artist_ids,
)
from typing import List

router = APIRouter(prefix="/artists", tags=["Artists"])


def _norm(value: str) -> str:
    return " ".join((value or "").split()).casefold()


@router.post("/", response_model=ArtistResponse)
def create_artist(payload: ArtistCreate, request: Request):
    tenant_id = request.state.tenant_id
    uid = ensure_authenticated(request)

    # Reutiliza un perfil SOLO si es tuyo (antes devolvía el perfil de otro usuario con el mismo nombre).
    want_name, want_type = _norm(payload.name), _norm(payload.type)
    for existing in CatalogService.get_artists(tenant_id=tenant_id):
        if (
            _norm(existing.name) == want_name
            and _norm(existing.type) == want_type
            and artist_accessible(request, existing, tenant_id)
        ):
            return existing

    artist = Artist(name=payload.name, type=payload.type, owner_user_id=uid)
    CatalogService.save_artist(artist, tenant_id=tenant_id)
    return artist


@router.get("/", response_model=List[ArtistResponse])
def list_artists(request: Request):
    tenant_id = request.state.tenant_id
    artists = CatalogService.get_artists(tenant_id=tenant_id)
    if not is_admin(request):
        uid = current_user_id(request)
        linked = user_release_artist_ids(request, tenant_id)
        artists = [
            a for a in artists
            if (a.owner_user_id or "") == uid or str(a.id) in linked
        ]
    return [a.to_dict() for a in artists]
