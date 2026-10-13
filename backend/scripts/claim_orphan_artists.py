"""
Migración: asigna propietario a artistas y portadas creados antes del aislamiento por cuenta.

Regla: si TODOS los releases que usan un artista/portada pertenecen al mismo usuario, ese usuario
pasa a ser el propietario. Si hay varios dueños distintos o ninguno, se deja sin tocar (solo lo ve admin).

Uso:
  python scripts/claim_orphan_artists.py            # simulación (no escribe nada)
  python scripts/claim_orphan_artists.py --apply    # aplica los cambios
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.paths import STORAGE_DIR, is_valid_tenant_id
from app.services.catalog_service import CatalogService


def run(apply: bool) -> None:
    tenants_dir = STORAGE_DIR / "tenants"
    if not tenants_dir.exists():
        print("No hay storage/tenants")
        return
    for tdir in sorted(p for p in tenants_dir.iterdir() if p.is_dir()):
        tenant = tdir.name
        if not is_valid_tenant_id(tenant):
            print(f"[{tenant}] ignorado: tenant_id inválido")
            continue
        releases = CatalogService.get_releases(tenant_id=tenant)
        artist_owners: dict[str, set] = {}
        art_owners: dict[str, set] = {}
        for r in releases:
            owner = getattr(r, "owner_user_id", None)
            if getattr(r, "artist_id", None):
                artist_owners.setdefault(str(r.artist_id), set()).add(owner)
            if getattr(r, "artwork_id", None):
                art_owners.setdefault(str(r.artwork_id), set()).add(owner)

        claimed_a = claimed_w = 0
        for artist in CatalogService.get_artists(tenant_id=tenant):
            if artist.owner_user_id:
                continue
            owners = artist_owners.get(str(artist.id), set())
            if len(owners) == 1 and None not in owners:
                print(f"[{tenant}] artista {artist.name!r} -> {next(iter(owners))}")
                claimed_a += 1
                if apply:
                    artist.owner_user_id = next(iter(owners))
                    CatalogService.save_artist(artist, tenant_id=tenant)

        for asset_id, owners in art_owners.items():
            asset = CatalogService.get_asset_by_id(asset_id, tenant_id=tenant)
            if not asset or asset.get("owner_user_id"):
                continue
            if len(owners) == 1 and None not in owners:
                print(f"[{tenant}] portada {asset_id} -> {next(iter(owners))}")
                claimed_w += 1
                if apply:
                    asset["owner_user_id"] = next(iter(owners))
                    CatalogService.save_asset(asset, tenant_id=tenant)
        print(f"[{tenant}] artistas: {claimed_a} | portadas: {claimed_w} ({'aplicado' if apply else 'simulación'})")


if __name__ == "__main__":
    run("--apply" in sys.argv)
