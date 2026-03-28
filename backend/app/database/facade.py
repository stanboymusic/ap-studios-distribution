"""
Dual-write facade.
Transparente para el resto del sistema:
- Si Postgres está disponible -> escribe en Postgres Y en archivos
- Si no está -> solo archivos (comportamiento actual)
El objetivo es llegar a un punto donde los archivos sean solo backup.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

_db_available: Optional[bool] = None


def _is_pg_available() -> bool:
    global _db_available
    if _db_available is None:
        try:
            from app.database.connection import is_db_available

            _db_available = is_db_available()
        except Exception:
            _db_available = False
    return _db_available


def get_session():
    from app.database.connection import SessionLocal

    if not SessionLocal:
        return None
    return SessionLocal()


class ArtistFacade:
    """Drop-in replacement for CatalogService artist methods."""

    @staticmethod
    def get_artists(tenant_id: str):
        from app.services.catalog_service import CatalogService

        if _is_pg_available():
            try:
                from app.database.repositories import artist_repo

                db = get_session()
                if db:
                    result = artist_repo.get_all(tenant_id, db)
                    db.close()
                    return result
            except Exception as e:
                logger.warning(f"PG get_artists failed, falling back: {e}")
        return CatalogService.get_artists(tenant_id=tenant_id)

    @staticmethod
    def save_artist(artist, tenant_id: str):
        from app.services.catalog_service import CatalogService

        CatalogService.save_artist(artist, tenant_id=tenant_id)
        if _is_pg_available():
            try:
                from app.database.repositories import artist_repo

                db = get_session()
                if db:
                    artist_repo.save(artist, tenant_id, db)
                    db.close()
            except Exception as e:
                logger.warning(f"PG save_artist failed (file backup ok): {e}")

    @staticmethod
    def get_artist_by_id(artist_id: UUID, tenant_id: str):
        from app.services.catalog_service import CatalogService

        if _is_pg_available():
            try:
                from app.database.repositories import artist_repo

                db = get_session()
                if db:
                    result = artist_repo.get_by_id(str(artist_id), tenant_id, db)
                    db.close()
                    if result:
                        return result
            except Exception as e:
                logger.warning(f"PG get_artist_by_id failed, falling back: {e}")
        return CatalogService.get_artist_by_id(artist_id, tenant_id=tenant_id)


class ReleaseFacade:
    """Drop-in replacement para CatalogService release methods."""

    @staticmethod
    def get_releases(tenant_id: str):
        from app.services.catalog_service import CatalogService

        if _is_pg_available():
            try:
                from app.database.repositories import release_repo

                db = get_session()
                if db:
                    result = release_repo.get_all(tenant_id, db)
                    db.close()
                    return result
            except Exception as e:
                logger.warning(f"PG get_releases failed, falling back: {e}")
        return CatalogService.get_releases(tenant_id=tenant_id)

    @staticmethod
    def save_release(release, tenant_id: str):
        from app.services.catalog_service import CatalogService

        CatalogService.save_release(release, tenant_id=tenant_id)
        if _is_pg_available():
            try:
                from app.database.repositories import release_repo

                db = get_session()
                if db:
                    release_repo.save(release, tenant_id, db)
                    db.close()
            except Exception as e:
                logger.warning(f"PG save_release failed (file backup ok): {e}")

    @staticmethod
    def get_release_by_id(release_id: UUID, tenant_id: str):
        from app.services.catalog_service import CatalogService

        if _is_pg_available():
            try:
                from app.database.repositories import release_repo

                db = get_session()
                if db:
                    result = release_repo.get_by_id(str(release_id), tenant_id, db)
                    db.close()
                    if result:
                        return result
            except Exception as e:
                logger.warning(f"PG get_release_by_id failed, falling back: {e}")
        return CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
