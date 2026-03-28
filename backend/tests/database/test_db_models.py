import pytest
from unittest.mock import patch, MagicMock

from app.models.artist import Artist
from app.models.release import ReleaseDraft


def test_artist_facade_falls_back_to_file(tmp_path, monkeypatch):
    """Si PG no está disponible, ArtistFacade usa file storage."""
    from app.database.facade import ArtistFacade

    monkeypatch.setattr("app.database.facade._db_available", False)

    artist = Artist(name="Test Artist", type="SOLO")
    with patch("app.services.catalog_service.CatalogService.save_artist") as mock_save:
        ArtistFacade.save_artist(artist, "default")
        mock_save.assert_called_once()


def test_release_facade_falls_back_to_file(monkeypatch):
    """Si PG no está disponible, ReleaseFacade usa file storage."""
    from app.database.facade import ReleaseFacade

    monkeypatch.setattr("app.database.facade._db_available", False)

    release = ReleaseDraft()
    release.title = "Test Release"
    with patch("app.services.catalog_service.CatalogService.save_release") as mock_save:
        ReleaseFacade.save_release(release, "default")
        mock_save.assert_called_once()


def test_db_models_importan_sin_error():
    """Los modelos ORM importan sin necesitar conexión activa."""
    from app.database.models import DBUser, DBArtist, DBRelease, DBTrack

    assert DBUser.__tablename__ == "users"
    assert DBArtist.__tablename__ == "artists"
    assert DBRelease.__tablename__ == "releases"
    assert DBTrack.__tablename__ == "tracks"


def test_user_facade_dual_write(monkeypatch):
    """Con PG disponible, user se guarda en ambos lados."""
    monkeypatch.setattr("app.database.facade._db_available", True)

    mock_db = MagicMock()
    with patch("app.database.facade.get_session", return_value=mock_db):
        with patch("app.database.repositories.artist_repo.save") as pg_save:
            with patch("app.services.catalog_service.CatalogService.save_artist") as file_save:
                from app.database.facade import ArtistFacade

                artist = Artist(name="Dual Write Test", type="SOLO")
                ArtistFacade.save_artist(artist, "default")
                file_save.assert_called_once()
                assert pg_save.called


def test_migrations_no_crash_sin_db():
    """run_migrations() no crashea si PG no está."""
    with patch("app.database.connection.DB_AVAILABLE", False):
        with patch("app.database.connection.engine", None):
            from app.database.migrations import run_migrations

            result = run_migrations()
            assert result is False
