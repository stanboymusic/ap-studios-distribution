"""
ERN Importer - parse external ERN XML and import into the catalog.
Two-step flow: parse (preview) -> confirm (create).
"""
from __future__ import annotations

import json
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.catalog.identifier_service import claim_manual_isrc, claim_manual_upc, create_upc
from app.core.paths import storage_path
from app.models.artist import Artist
from app.models.release import ReleaseDraft
from app.repositories import catalog_repository as cat_repo
from app.services.catalog_service import CatalogService


ERN_NAMESPACE_MAP = {
    "urn:ern:std:ern:ernm:v34": "3.4",
    "urn:ern:std:ern:ernm:v36": "3.6",
    "http://ddex.net/xml/ern/382": "3.8.2",
    "http://ddex.net/xml/ern/383": "3.8.3",
}

IMPORT_PREVIEW_DIR = storage_path("ern_import_preview")
PREVIEW_TTL_SECONDS = 30 * 60


class ERNParseError(Exception):
    pass


class ERNImporter:
    def detect_version(self, xml_content: str) -> str:
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            raise ERNParseError(f"Invalid XML: {exc}") from exc

        tag = root.tag
        if not tag.startswith("{"):
            raise ERNParseError("Missing XML namespace (not a valid ERN)")

        ns = tag[1:tag.index("}")]
        if ns in ERN_NAMESPACE_MAP:
            return ERN_NAMESPACE_MAP[ns]

        if ns.startswith("http://ddex.net/xml/ern/4"):
            suffix = ns.rsplit("/", 1)[-1]
            if suffix.isdigit():
                if len(suffix) == 1:
                    return "4.0"
                return "4." + ".".join(list(suffix[1:]))
            return "4.x"

        raise ERNParseError(f"Unknown ERN namespace: {ns}")

    def parse(self, xml_content: str, tenant_id: str) -> dict:
        version = self.detect_version(xml_content)
        root = ET.fromstring(xml_content)
        ns = _extract_namespace(root)
        p = f"{{{ns}}}"

        release_node = _find_main_release(root, p)
        if release_node is None:
            raise ERNParseError("No main Release found in ERN (Album/Single expected)")

        release = self._extract_release(release_node, p)
        tracks = self._extract_tracks(root, p, release)

        upc_conflict, isrc_conflicts = self._check_conflicts(
            release["upc"], [t["isrc"] for t in tracks], tenant_id
        )
        warnings = []
        if upc_conflict:
            warnings.append(f"UPC {release['upc']} already exists in catalog")

        for track in tracks:
            if track["isrc"] in isrc_conflicts:
                track["conflict"] = True
                track["skipped"] = False
            else:
                track["conflict"] = False
                track["skipped"] = False

        preview = {
            "preview_id": None,
            "version": version,
            "release": release,
            "tracks": tracks,
            "upc_conflict": upc_conflict,
            "warnings": warnings,
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        }
        preview_id = self._save_preview(preview, tenant_id, xml_content)
        preview["preview_id"] = preview_id
        return preview

    def _extract_release(self, node: ET.Element, p: str) -> dict:
        upc = (
            _find_text(node, f".//{p}ReleaseId/{p}ICPN")
            or _find_text(node, f".//{p}ReleaseId/{p}UPC")
            or ""
        )
        if not upc:
            raise ERNParseError("ERN has no UPC/ICPN - cannot import without identifier")

        title = (
            _find_text(node, f".//{p}ReferenceTitle/{p}TitleText")
            or _find_text(node, f".//{p}Title/{p}TitleText")
            or _find_text(node, f".//{p}DisplayTitle/{p}TitleText")
            or ""
        )
        subtitle = _find_text(node, f".//{p}ReferenceTitle/{p}SubTitle")
        artist_name = (
            _find_text(node, f".//{p}DisplayArtistName/{p}FullName")
            or _find_text(node, f".//{p}DisplayArtistName")
            or _find_text(node, f".//{p}ArtistName/{p}FullName")
            or ""
        )
        release_date = (
            _find_text(node, f".//{p}ReleaseDate")
            or _find_text(node, f".//{p}OriginalReleaseDate")
            or ""
        )
        label = _find_text(node, f".//{p}LabelName")
        genre = _find_text(node, f".//{p}Genre/{p}GenreText")
        territory = _find_text(node, f".//{p}TerritoryCode") or "Worldwide"
        language = (
            node.get("LanguageAndScriptCode")
            or _find_text(node, f".//{p}LanguageOfPerformance")
            or "en"
        )
        release_type = _find_text(node, f"{p}ReleaseType") or ""

        return {
            "upc": upc,
            "title": title,
            "subtitle": subtitle,
            "artist_name": artist_name,
            "release_date": release_date,
            "label": label,
            "genre": genre,
            "territory": territory,
            "language": language,
            "release_type": release_type,
        }

    def _extract_tracks(self, root: ET.Element, p: str, release: dict) -> list[dict]:
        tracks: list[dict] = []
        for sr_node in root.findall(f".//{p}SoundRecording"):
            isrc = (
                _find_text(sr_node, f".//{p}SoundRecordingId/{p}ISRC")
                or _find_text(sr_node, f".//{p}ISRC")
                or ""
            )
            if not isrc:
                continue

            track_title = (
                _find_text(sr_node, f".//{p}ReferenceTitle/{p}TitleText")
                or _find_text(sr_node, f".//{p}Title/{p}TitleText")
                or release["title"]
            )
            track_artist = (
                _find_text(sr_node, f".//{p}DisplayArtistName/{p}FullName")
                or release["artist_name"]
            )
            seq_str = _find_text(sr_node, f".//{p}SequenceNumber") or "0"
            try:
                seq = int(seq_str)
            except ValueError:
                seq = 0
            duration = _find_text(sr_node, f".//{p}Duration")
            parental = _find_text(sr_node, f".//{p}ParentalWarningType") or ""
            explicit = parental.strip().lower() in {"explicit", "explicitcontentedited"}
            track_genre = _find_text(sr_node, f".//{p}Genre/{p}GenreText")

            tracks.append(
                {
                    "isrc": isrc,
                    "title": track_title,
                    "artist_name": track_artist,
                    "sequence": seq,
                    "duration": duration,
                    "explicit": explicit,
                    "genre": track_genre,
                }
            )

        tracks.sort(key=lambda t: t["sequence"])
        return tracks

    def _check_conflicts(
        self, upc: str, isrcs: list[str], tenant_id: str
    ) -> tuple[bool, list[str]]:
        upc_conflict = _upc_exists(tenant_id, upc) or cat_repo.is_upc_reserved(tenant_id, upc)
        conflicts: list[str] = []
        for isrc in isrcs:
            if _isrc_exists(tenant_id, isrc) or cat_repo.is_isrc_reserved(tenant_id, isrc):
                conflicts.append(isrc)
        return upc_conflict, conflicts

    def _save_preview(self, preview: dict, tenant_id: str, xml_content: str) -> str:
        preview_id = f"prev-{uuid.uuid4().hex}"
        target_dir = IMPORT_PREVIEW_DIR / tenant_id
        target_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        record = dict(preview)
        record["preview_id"] = preview_id
        record["original_xml"] = xml_content
        record["expires_at"] = (now.timestamp() + PREVIEW_TTL_SECONDS)
        path = target_dir / f"{preview_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return preview_id

    def _load_preview(self, preview_id: str, tenant_id: str) -> dict:
        path = IMPORT_PREVIEW_DIR / tenant_id / f"{preview_id}.json"
        if not path.exists():
            raise ERNParseError("Preview not found or expired")
        record = json.loads(path.read_text(encoding="utf-8"))
        expires_at = record.get("expires_at")
        if expires_at is not None and float(expires_at) < datetime.now(timezone.utc).timestamp():
            try:
                path.unlink()
            except Exception:
                pass
            raise ERNParseError("Preview not found or expired")
        return record

    def delete_preview(self, preview_id: str, tenant_id: str) -> None:
        path = IMPORT_PREVIEW_DIR / tenant_id / f"{preview_id}.json"
        if path.exists():
            path.unlink()

    def confirm(self, preview_id: str, overrides: dict, tenant_id: str) -> dict:
        preview = self._load_preview(preview_id, tenant_id)
        release_data = preview["release"].copy()
        release_data.update({k: v for k, v in overrides.items() if v is not None})

        upc = release_data["upc"]
        upc_conflict = bool(preview.get("upc_conflict"))
        used_upc = upc
        if overrides.get("force_new_upc") or upc_conflict:
            used_upc = create_upc(tenant_id=tenant_id)
        else:
            try:
                claim_manual_upc(used_upc, tenant_id=tenant_id)
            except Exception:
                used_upc = create_upc(tenant_id=tenant_id)

        artist_name = (release_data.get("artist_name") or "Unknown").strip()
        artist = CatalogService.find_artist_by_name(artist_name, "SOLO", tenant_id=tenant_id)
        if not artist:
            artist = Artist(name=artist_name, type="SOLO")
            CatalogService.save_artist(artist, tenant_id=tenant_id)

        release = ReleaseDraft()
        release.title = release_data.get("title") or ""
        release.release_type = release_data.get("release_type") or "Album"
        release.original_release_date = _parse_date(release_data.get("release_date"))
        release.language = release_data.get("language") or "en"
        release.territories = [release_data.get("territory") or "Worldwide"]
        release.artist_id = artist.id
        release.upc = used_upc
        release.tracks = []
        release.track_ids = []

        created_isrcs: list[str] = []
        created_tracks = 0
        skipped_details = []

        try:
            cat_repo.create_release(tenant_id, release)
            for track in preview["tracks"]:
                if track.get("conflict"):
                    skipped_details.append(
                        {"isrc": track["isrc"], "reason": "already_exists"}
                    )
                    continue

                try:
                    claim_manual_isrc(track["isrc"], tenant_id=tenant_id)
                except ValueError as exc:
                    msg = str(exc).lower()
                    if "exists" in msg or "reserved" in msg:
                        skipped_details.append(
                            {"isrc": track["isrc"], "reason": "already_exists"}
                        )
                        continue
                    raise

                created_isrcs.append(track["isrc"])
                track_id = f"TRK-{uuid.uuid4()}"
                entry = {
                    "track_id": track_id,
                    "title": track["title"],
                    "track_number": track["sequence"],
                    "duration_seconds": _parse_duration_seconds(track.get("duration")),
                    "explicit": track.get("explicit", False),
                    "isrc": track["isrc"],
                }
                cat_repo.create_track(tenant_id, str(release.id), entry)
                created_tracks += 1
            return {
                "release_id": str(release.id),
                "tracks_created": created_tracks,
                "tracks_skipped": len(skipped_details),
                "skipped_details": skipped_details,
                "status": "imported",
            }
        except Exception as exc:
            cat_repo.delete_release(tenant_id, str(release.id))
            _rollback_identifiers(tenant_id, used_upc, created_isrcs)
            raise exc


def detect_ern_version(xml_content: str) -> str:
    return ERNImporter().detect_version(xml_content)


def _find_main_release(root: ET.Element, p: str) -> Optional[ET.Element]:
    for release in root.findall(f".//{p}Release"):
        release_type = _find_text(release, f"{p}ReleaseType")
        if release_type in {"Album", "Single", "EP", "Bundle"}:
            return release
    return root.find(f".//{p}Release")


def _find_text(node: ET.Element, path: str) -> Optional[str]:
    el = node.find(path)
    if el is not None and el.text:
        return el.text.strip()
    return None


def _upc_exists(tenant_id: str, upc: str) -> bool:
    want = (upc or "").strip()
    if not want:
        return False
    for release in CatalogService.get_releases(tenant_id=tenant_id):
        value = (getattr(release, "upc", "") or "").strip()
        if value == want:
            return True
    return False


def _isrc_exists(tenant_id: str, isrc: str) -> bool:
    want = (isrc or "").strip().upper()
    if not want:
        return False
    for release in CatalogService.get_releases(tenant_id=tenant_id):
        release_isrc = (getattr(release, "isrc", "") or "").strip().upper()
        if release_isrc and release_isrc == want:
            return True
        for track in (getattr(release, "tracks", None) or []):
            if not isinstance(track, dict):
                continue
            value = (track.get("isrc") or "").strip().upper()
            if value == want:
                return True
    return False


def _parse_date(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_duration_seconds(value: Optional[str]) -> float:
    if not value:
        return 0.0
    text = str(value).strip().upper()
    if not text.startswith("PT"):
        return 0.0
    hours = minutes = seconds = 0.0
    text = text[2:]
    num = ""
    for ch in text:
        if ch.isdigit() or ch == ".":
            num += ch
            continue
        if ch == "H":
            hours = float(num or 0)
        elif ch == "M":
            minutes = float(num or 0)
        elif ch == "S":
            seconds = float(num or 0)
        num = ""
    return round(hours * 3600 + minutes * 60 + seconds, 2)


def _rollback_identifiers(tenant_id: str, upc: str, isrcs: list[str]) -> None:
    if not upc and not isrcs:
        return

    def _rollback(state):
        if upc:
            state.reserved_upc.pop(upc, None)
        for isrc in isrcs:
            state.reserved_isrc.pop(isrc, None)

    try:
        cat_repo._mutate_state(tenant_id, _rollback)
    except Exception:
        pass


def _extract_namespace(root: ET.Element) -> str:
    tag = root.tag
    if not tag.startswith("{"):
        raise ERNParseError("Missing XML namespace (not a valid ERN)")
    return tag[1:tag.index("}")]
