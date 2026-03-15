from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import requests

from app.catalog.isrc_generator import generate_isrc, normalize_isrc, validate_isrc_format
from app.catalog.upc_generator import generate_upc, validate_upc
from app.core.paths import storage_path
from app.repositories.catalog_repository import (
    IDENTIFIER_SCOPE,
    get_next_isrc_sequence,
    get_next_upc_sequence,
    is_isrc_reserved,
    is_upc_reserved,
    reserve_isrc,
    reserve_upc,
)
from app.services.catalog_service import CatalogService


ISRC_COUNTRY = (os.getenv("ISRC_COUNTRY") or "US").strip().upper()
ISRC_REGISTRANT = (os.getenv("ISRC_REGISTRANT") or "APS").strip().upper()
UPC_PREFIX = (os.getenv("UPC_PREFIX") or "859").strip()
IDENTIFIER_GLOBAL_CHECK = (os.getenv("IDENTIFIER_GLOBAL_CHECK") or "false").strip().lower() in {"1", "true", "yes"}


def _scope_tenants(tenant_id: str) -> list[str]:
    if IDENTIFIER_SCOPE != "global":
        return [tenant_id]

    tenants_root = storage_path("tenants")
    tenant_ids: list[str] = []
    if tenants_root.exists():
        for child in tenants_root.iterdir():
            if child.is_dir():
                tenant_ids.append(child.name)
    if "default" not in tenant_ids:
        tenant_ids.append("default")
    return tenant_ids


def _track_isrcs(tenant_id: str) -> set[str]:
    used: set[str] = set()
    for scoped_tenant in _scope_tenants(tenant_id):
        for release in CatalogService.get_releases(tenant_id=scoped_tenant):
            release_isrc = normalize_isrc(getattr(release, "isrc", "") or "")
            if release_isrc:
                used.add(release_isrc)
            for track in (getattr(release, "tracks", None) or []):
                if not isinstance(track, dict):
                    continue
                value = normalize_isrc(track.get("isrc") or "")
                if value:
                    used.add(value)
    return used


def _release_upcs(tenant_id: str) -> set[str]:
    used: set[str] = set()
    for scoped_tenant in _scope_tenants(tenant_id):
        for release in CatalogService.get_releases(tenant_id=scoped_tenant):
            value = str(getattr(release, "upc", "") or "").strip()
            if value:
                used.add(value)
    return used


def check_isrc_global(isrc: str, timeout_seconds: float = 5.0) -> bool:
    candidate = normalize_isrc(isrc)
    url = f"https://musicbrainz.org/ws/2/recording?query=isrc:{candidate}&fmt=json"
    try:
        response = requests.get(url, timeout=timeout_seconds, headers={"User-Agent": "APStudiosDistribution/1.0"})
        response.raise_for_status()
        payload = response.json()
        return int(payload.get("count", 0)) > 0
    except Exception:
        # External check should not block local operations if service is unavailable.
        return False


def _is_isrc_available(isrc: str, tenant_id: str) -> bool:
    candidate = normalize_isrc(isrc)
    if candidate in _track_isrcs(tenant_id):
        return False
    if is_isrc_reserved(tenant_id, candidate):
        return False
    return True


def _is_upc_available(upc: str, tenant_id: str) -> bool:
    candidate = (upc or "").strip()
    if candidate in _release_upcs(tenant_id):
        return False
    if is_upc_reserved(tenant_id, candidate):
        return False
    return True


def create_isrc(
    tenant_id: str = "default",
    *,
    country: str | None = None,
    registrant: str | None = None,
    source: str = "system",
    check_global: bool | None = None,
) -> str:
    cc = (country or ISRC_COUNTRY).strip().upper()
    reg = (registrant or ISRC_REGISTRANT).strip().upper()
    yy = datetime.utcnow().strftime("%y")
    should_check_global = IDENTIFIER_GLOBAL_CHECK if check_global is None else bool(check_global)

    for _ in range(100000):
        seq = get_next_isrc_sequence(tenant_id, yy)
        candidate = generate_isrc(cc, reg, seq, year=yy)
        if not _is_isrc_available(candidate, tenant_id):
            continue
        if should_check_global and check_isrc_global(candidate):
            continue
        if reserve_isrc(tenant_id, candidate, source=source):
            return candidate
    raise RuntimeError("Unable to generate unique ISRC")


def create_upc(
    tenant_id: str = "default",
    *,
    prefix: str | None = None,
    source: str = "system",
) -> str:
    pref = (prefix or UPC_PREFIX).strip()

    for _ in range(500000):
        seq = get_next_upc_sequence(tenant_id, pref)
        candidate = generate_upc(pref, seq)
        if not _is_upc_available(candidate, tenant_id):
            continue
        if reserve_upc(tenant_id, candidate, source=source):
            return candidate
    raise RuntimeError("Unable to generate unique UPC")


def claim_manual_isrc(isrc: str, tenant_id: str = "default", source: str = "manual") -> str:
    candidate = normalize_isrc(isrc)
    if not validate_isrc_format(candidate):
        raise ValueError("Invalid ISRC format")
    if not _is_isrc_available(candidate, tenant_id):
        raise ValueError("ISRC already exists in catalog")
    if not reserve_isrc(tenant_id, candidate, source=source):
        raise ValueError("ISRC already reserved")
    return candidate


def claim_manual_upc(upc: str, tenant_id: str = "default", source: str = "manual") -> str:
    candidate = (upc or "").strip()
    if not validate_upc(candidate):
        raise ValueError("Invalid UPC format/checksum")
    if not _is_upc_available(candidate, tenant_id):
        raise ValueError("UPC already exists in catalog")
    if not reserve_upc(tenant_id, candidate, source=source):
        raise ValueError("UPC already reserved")
    return candidate
