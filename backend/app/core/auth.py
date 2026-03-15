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

