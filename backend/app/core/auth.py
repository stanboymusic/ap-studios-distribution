from __future__ import annotations

from fastapi import HTTPException, Request


ADMIN_ROLES = {"admin", "staff"}
ARTIST_ROLES = {"artist"}


def current_role(request: Request) -> str:
    return (getattr(request.state, "user_role", None) or "artist").strip().lower()


def current_user_id(request: Request) -> str:
    return (getattr(request.state, "user_id", None) or "anonymous").strip()


def is_admin(request: Request) -> bool:
    return current_role(request) in ADMIN_ROLES


def is_artist(request: Request) -> bool:
    return current_role(request) in ARTIST_ROLES


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")


def ensure_release_access(request: Request, release_obj) -> None:
    if is_admin(request):
        return

    owner_user_id = (getattr(release_obj, "owner_user_id", None) or "").strip()
    req_user_id = current_user_id(request)
    if owner_user_id and owner_user_id == req_user_id:
        return

    raise HTTPException(status_code=403, detail="You do not have access to this release")



def ensure_authenticated(request: Request) -> str:
    """Devuelve el user_id autenticado o lanza 401."""
    uid = current_user_id(request)
    if not uid or uid == "anonymous" or uid.endswith(":anonymous"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return uid


def user_release_artist_ids(request: Request, tenant_id: str) -> set[str]:
    """IDs de artistas referenciados por releases que pertenecen al usuario (datos legacy sin owner)."""
    from app.services.catalog_service import CatalogService

    uid = current_user_id(request)
    ids: set[str] = set()
    for r in CatalogService.get_releases(tenant_id=tenant_id):
        if (getattr(r, "owner_user_id", None) or "") == uid and getattr(r, "artist_id", None):
            ids.add(str(r.artist_id))
    return ids


def artist_accessible(request: Request, artist, tenant_id: str) -> bool:
    """Admin ve todo; un artista solo ve perfiles propios (o ligados a sus releases)."""
    if is_admin(request):
        return True
    uid = current_user_id(request)
    if (getattr(artist, "owner_user_id", None) or "") == uid:
        return True
    return str(artist.id) in user_release_artist_ids(request, tenant_id)
