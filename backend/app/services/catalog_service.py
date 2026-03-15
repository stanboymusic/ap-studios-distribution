import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime
from app.models.release import ReleaseDraft
from app.models.artist import Artist
from app.core.paths import tenant_path, storage_path

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

class CatalogService:
    @staticmethod
    def _normalize_artist_name(name: str) -> str:
        return " ".join((name or "").split()).casefold()

    @staticmethod
    def _catalog_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "catalog")

    @staticmethod
    def _legacy_catalog_dir() -> Path:
        # Backwards compatibility (pre-multi-tenant)
        return storage_path("catalog")

    @staticmethod
    def _files(tenant_id: str) -> Dict[str, Path]:
        base = CatalogService._catalog_dir(tenant_id)
        return {
            "releases": base / "releases.json",
            "artists": base / "artists.json",
            "assets": base / "assets.json",
            "delivery_events": base / "delivery_events.json",
        }

    @staticmethod
    def _ensure_catalog(tenant_id: str):
        base = CatalogService._catalog_dir(tenant_id)
        base.mkdir(parents=True, exist_ok=True)
        files = CatalogService._files(tenant_id)
        for file in files.values():
            if not file.exists():
                with open(file, "w", encoding="utf-8") as f:
                    json.dump([], f)

    @staticmethod
    def _load_json(file_path: Path, tenant_id: str) -> List[Dict[str, Any]]:
        CatalogService._ensure_catalog(tenant_id)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_json(file_path: Path, data: List[Dict[str, Any]], tenant_id: str):
        CatalogService._ensure_catalog(tenant_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=json_serial)

    # --- Artist Methods ---
    @staticmethod
    def get_artists(tenant_id: str = "default") -> List[Artist]:
        files = CatalogService._files(tenant_id)
        data = CatalogService._load_json(files["artists"], tenant_id)
        # Auto-migrate legacy catalog into default tenant if tenant is default and empty
        if tenant_id == "default" and not data:
            legacy_file = CatalogService._legacy_catalog_dir() / "artists.json"
            if legacy_file.exists():
                try:
                    legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                    if isinstance(legacy, list) and legacy:
                        CatalogService._save_json(files["artists"], legacy, tenant_id)
                        data = legacy
                except Exception:
                    pass
        return [Artist.from_dict(item) for item in data]

    @staticmethod
    def save_artist(artist: Artist, tenant_id: str = "default"):
        files = CatalogService._files(tenant_id)
        artists = CatalogService._load_json(files["artists"], tenant_id)
        existing = next((i for i, a in enumerate(artists) if a["id"] == str(artist.id)), None)
        if existing is not None:
            artists[existing] = artist.to_dict()
        else:
            artists.append(artist.to_dict())
        CatalogService._save_json(files["artists"], artists, tenant_id)

    @staticmethod
    def get_artist_by_id(artist_id: UUID, tenant_id: str = "default") -> Optional[Artist]:
        artists = CatalogService.get_artists(tenant_id=tenant_id)
        return next((a for a in artists if a.id == artist_id), None)

    @staticmethod
    def find_artist_by_name(name: str, type: str, tenant_id: str = "default") -> Optional[Artist]:
        want_name = CatalogService._normalize_artist_name(name)
        want_type = (type or "").strip().casefold()
        for artist in CatalogService.get_artists(tenant_id=tenant_id):
            if (
                CatalogService._normalize_artist_name(artist.name) == want_name
                and (artist.type or "").strip().casefold() == want_type
            ):
                return artist
        return None

    # --- Release Methods ---
    @staticmethod
    def get_releases(tenant_id: str = "default") -> List[ReleaseDraft]:
        files = CatalogService._files(tenant_id)
        data = CatalogService._load_json(files["releases"], tenant_id)
        if tenant_id == "default" and not data:
            legacy_file = CatalogService._legacy_catalog_dir() / "releases.json"
            if legacy_file.exists():
                try:
                    legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                    if isinstance(legacy, list) and legacy:
                        CatalogService._save_json(files["releases"], legacy, tenant_id)
                        data = legacy
                except Exception:
                    pass
        return [ReleaseDraft.from_dict(item) for item in data]

    @staticmethod
    def save_release(release: ReleaseDraft, tenant_id: str = "default"):
        files = CatalogService._files(tenant_id)
        releases = CatalogService._load_json(files["releases"], tenant_id)
        existing = next((i for i, r in enumerate(releases) if r["id"] == str(release.id)), None)
        if existing is not None:
            releases[existing] = release.to_dict()
        else:
            releases.append(release.to_dict())
        CatalogService._save_json(files["releases"], releases, tenant_id)

    @staticmethod
    def get_release_by_id(release_id: UUID, tenant_id: str = "default") -> Optional[ReleaseDraft]:
        releases = CatalogService.get_releases(tenant_id=tenant_id)
        return next((r for r in releases if r.id == release_id), None)

    # --- Asset Methods ---
    @staticmethod
    def get_assets(tenant_id: str = "default") -> List[Dict[str, Any]]:
        files = CatalogService._files(tenant_id)
        data = CatalogService._load_json(files["assets"], tenant_id)
        if tenant_id == "default" and not data:
            legacy_file = CatalogService._legacy_catalog_dir() / "assets.json"
            if legacy_file.exists():
                try:
                    legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                    if isinstance(legacy, list) and legacy:
                        CatalogService._save_json(files["assets"], legacy, tenant_id)
                        data = legacy
                except Exception:
                    pass
        return data

    @staticmethod
    def save_asset(asset_data: Dict[str, Any], tenant_id: str = "default"):
        files = CatalogService._files(tenant_id)
        assets = CatalogService._load_json(files["assets"], tenant_id)
        existing = next((i for i, a in enumerate(assets) if a["id"] == asset_data["id"]), None)
        if existing is not None:
            assets[existing] = asset_data
        else:
            assets.append(asset_data)
        CatalogService._save_json(files["assets"], assets, tenant_id)

    @staticmethod
    def get_asset_by_id(asset_id: str, tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        assets = CatalogService.get_assets(tenant_id=tenant_id)
        return next((a for a in assets if a["id"] == asset_id), None)

    # --- Delivery Event Methods ---
    @staticmethod
    def get_delivery_events(tenant_id: str = "default") -> List[Dict[str, Any]]:
        files = CatalogService._files(tenant_id)
        data = CatalogService._load_json(files["delivery_events"], tenant_id)
        if tenant_id == "default" and not data:
            legacy_file = CatalogService._legacy_catalog_dir() / "delivery_events.json"
            if legacy_file.exists():
                try:
                    legacy = json.loads(legacy_file.read_text(encoding="utf-8"))
                    if isinstance(legacy, list) and legacy:
                        CatalogService._save_json(files["delivery_events"], legacy, tenant_id)
                        data = legacy
                except Exception:
                    pass
        return data

    @staticmethod
    def get_delivery_events_for_release(release_id: UUID, tenant_id: str = "default") -> List[Dict[str, Any]]:
        events = CatalogService.get_delivery_events(tenant_id=tenant_id)
        rid = str(release_id)
        return [e for e in events if e.get("release_id") == rid]

    @staticmethod
    def save_delivery_event(event_data: Dict[str, Any], tenant_id: str = "default"):
        files = CatalogService._files(tenant_id)
        events = CatalogService._load_json(files["delivery_events"], tenant_id)
        events.append(event_data)
        CatalogService._save_json(files["delivery_events"], events, tenant_id)
