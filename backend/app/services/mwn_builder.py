"""
MWN builder for DDEX Musical Work Claim Notification messages.
Reference: https://github.com/TheMLC/ddex-messages-mwn-notification
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Optional
import xml.etree.ElementTree as ET

MWN_NAMESPACE = "http://ddex.net/xml/mwn/14"
MWN_VERSION = "MWN/14"
MWN_DEFAULT_LANGUAGE = "en"
MWN_PROPRIETARY_NAMESPACE = "APSTUDIOS"


class MWNBuildError(Exception):
    """Raised when an MWN message cannot be built."""


def build_mwn_message(
    rights_config: dict,
    release: dict,
    sender_dpid: str,
    recipient_dpid: str,
) -> str:
    """
    Build a minimal MusicalWorkClaimNotificationMessage.
    """
    _validate_rights_config(rights_config, release)

    ET.register_namespace("", MWN_NAMESPACE)
    root = ET.Element(f"{{{MWN_NAMESPACE}}}MusicalWorkNotificationMessage")
    root.set("MessageSchemaVersionId", MWN_VERSION)

    _add_message_header(root, sender_dpid, recipient_dpid)

    parties = _collect_parties(rights_config)
    party_refs = _add_party_list(root, parties)

    work_ref = "W1"
    _add_work_list(root, rights_config, release, party_refs, work_ref)

    resource_refs = _add_resource_list(root, release, work_ref)
    _add_release_list(root, release, resource_refs)

    if hasattr(ET, "indent"):
        ET.indent(root, space="  ")

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def _validate_rights_config(rights_config: dict, release: dict) -> None:
    if not rights_config.get("work_title") and not release.get("title"):
        raise MWNBuildError("work_title or release title is required for MWN")
    if not release.get("upc"):
        raise MWNBuildError(
            f"Release {release.get('id')} has no UPC - cannot build MWN."
        )
    if not rights_config.get("composers") and not rights_config.get("publishers"):
        raise MWNBuildError(
            "At least one composer or publisher is required in rights config"
        )


def _resolve_language(rights_config: dict, release: dict) -> str:
    lang = (rights_config.get("language") or release.get("language") or "").strip()
    if not lang:
        return MWN_DEFAULT_LANGUAGE
    if re.match(r"^[a-zA-Z]{2,3}(-[a-zA-Z]+){0,1}(-[a-zA-Z]{2}|-[0-9]{3}){0,1}(-[a-zA-Z][a-zA-Z0-9]{4}[a-zA-Z0-9]*){0,1}$", lang):
        return lang
    return MWN_DEFAULT_LANGUAGE


def _add_message_header(root: ET.Element, sender_dpid: str, recipient_dpid: str) -> None:
    header = ET.SubElement(root, f"{{{MWN_NAMESPACE}}}MessageHeader")
    msg_id = ET.SubElement(header, f"{{{MWN_NAMESPACE}}}MessageId")
    msg_id.text = uuid.uuid4().hex.upper()

    sender = ET.SubElement(header, f"{{{MWN_NAMESPACE}}}MessageSender")
    sender_id = ET.SubElement(sender, f"{{{MWN_NAMESPACE}}}PartyId")
    sender_id.text = sender_dpid

    recipient = ET.SubElement(header, f"{{{MWN_NAMESPACE}}}MessageRecipient")
    recipient_id = ET.SubElement(recipient, f"{{{MWN_NAMESPACE}}}PartyId")
    recipient_id.text = recipient_dpid

    created_at = ET.SubElement(header, f"{{{MWN_NAMESPACE}}}MessageCreatedDateTime")
    created_at.text = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _collect_parties(rights_config: dict) -> list[dict]:
    parties: list[dict] = []
    for composer in rights_config.get("composers", []) or []:
        parties.append(
            {
                "name": composer.get("name") or "Unknown",
                "role": composer.get("role") or "composer",
                "ipi_name_number": composer.get("ipi_name_number"),
                "recipient_dpid": composer.get("recipient_dpid"),
                "is_org": False,
            }
        )
    for publisher in rights_config.get("publishers", []) or []:
        parties.append(
            {
                "name": publisher.get("name") or "Unknown",
                "role": publisher.get("role") or "publisher",
                "ipi_name_number": publisher.get("ipi_name_number"),
                "recipient_dpid": publisher.get("recipient_dpid"),
                "is_org": True,
            }
        )
    return parties


def _add_party_list(root: ET.Element, parties: list[dict]) -> dict[str, str]:
    party_refs: dict[str, str] = {}
    if not parties:
        return party_refs

    party_list = ET.SubElement(root, f"{{{MWN_NAMESPACE}}}PartyList")
    for idx, party in enumerate(parties, start=1):
        party_ref = f"P{idx}"
        party_node = ET.SubElement(party_list, f"{{{MWN_NAMESPACE}}}Party")

        party_id = ET.SubElement(party_node, f"{{{MWN_NAMESPACE}}}PartyId")
        if party.get("ipi_name_number"):
            ipi = ET.SubElement(party_id, f"{{{MWN_NAMESPACE}}}IpiNameNumber")
            ipi.text = str(party["ipi_name_number"]).strip()
        prop = ET.SubElement(party_id, f"{{{MWN_NAMESPACE}}}ProprietaryId")
        prop.set("Namespace", MWN_PROPRIETARY_NAMESPACE)
        prop.text = f"{MWN_PROPRIETARY_NAMESPACE}-{idx}"
        if party.get("recipient_dpid"):
            prop_dpid = ET.SubElement(party_id, f"{{{MWN_NAMESPACE}}}ProprietaryId")
            prop_dpid.set("Namespace", "DPID")
            prop_dpid.text = str(party["recipient_dpid"]).strip()

        party_ref_node = ET.SubElement(party_node, f"{{{MWN_NAMESPACE}}}PartyReference")
        party_ref_node.text = party_ref

        party_name = ET.SubElement(party_node, f"{{{MWN_NAMESPACE}}}PartyName")
        full_name = ET.SubElement(party_name, f"{{{MWN_NAMESPACE}}}FullName")
        full_name.text = party["name"]

        is_org = ET.SubElement(party_node, f"{{{MWN_NAMESPACE}}}IsOrganization")
        is_org.text = "true" if party.get("is_org") else "false"

        party_refs[party_ref] = party.get("role") or "composer"

    return party_refs


def _add_work_list(
    root: ET.Element,
    rights_config: dict,
    release: dict,
    party_refs: dict[str, str],
    work_ref: str,
) -> None:
    work_list = ET.SubElement(root, f"{{{MWN_NAMESPACE}}}WorkList")
    work = ET.SubElement(work_list, f"{{{MWN_NAMESPACE}}}MusicalWork")

    work_ref_node = ET.SubElement(work, f"{{{MWN_NAMESPACE}}}MusicalWorkReference")
    work_ref_node.text = work_ref

    work_id = ET.SubElement(work, f"{{{MWN_NAMESPACE}}}MusicalWorkId")
    iswc = rights_config.get("iswc")
    if iswc:
        iswc_node = ET.SubElement(work_id, f"{{{MWN_NAMESPACE}}}ISWC")
        iswc_node.text = str(iswc).strip()
    work_prop = ET.SubElement(work_id, f"{{{MWN_NAMESPACE}}}ProprietaryId")
    work_prop.set("Namespace", MWN_PROPRIETARY_NAMESPACE)
    work_prop.text = str(rights_config.get("id") or release.get("id") or uuid.uuid4().hex)

    title = ET.SubElement(work, f"{{{MWN_NAMESPACE}}}Title")
    title_text = ET.SubElement(title, f"{{{MWN_NAMESPACE}}}TitleText")
    title_text.text = rights_config.get("work_title") or release.get("title") or "Untitled"

    for party_ref, role in party_refs.items():
        role_text = (role or "").strip().lower()
        if role_text in {"publisher", "sub_publisher", "administrator"} or "publisher" in role_text:
            continue
        writer = ET.SubElement(work, f"{{{MWN_NAMESPACE}}}Writer")
        writer_ref = ET.SubElement(writer, f"{{{MWN_NAMESPACE}}}WriterPartyReference")
        writer_ref.text = party_ref
        role_node = ET.SubElement(writer, f"{{{MWN_NAMESPACE}}}Role")
        role_node.text = _map_writer_role(role)


def _normalize_tracks(release: dict) -> list[dict]:
    tracks = []
    for track in release.get("tracks", []) or []:
        tracks.append(
            {
                "title": track.get("title") or release.get("title") or "Unknown",
                "isrc": (track.get("isrc") or "").strip().upper() or None,
                "track_id": track.get("track_id") or track.get("id") or None,
            }
        )
    if not tracks:
        for idx, isrc in enumerate(release.get("isrcs", []) or [], start=1):
            tracks.append(
                {
                    "title": release.get("title") or "Unknown",
                    "isrc": (isrc or "").strip().upper() or None,
                    "track_id": f"track-{idx}",
                }
            )
    if not tracks:
        tracks.append(
            {
                "title": release.get("title") or "Unknown",
                "isrc": (release.get("isrc") or "").strip().upper() or None,
                "track_id": "track-1",
            }
        )
    return tracks


def _add_resource_list(root: ET.Element, release: dict, work_ref: str) -> list[str]:
    tracks = _normalize_tracks(release)
    resource_refs = []
    if not tracks:
        return resource_refs

    resource_list = ET.SubElement(root, f"{{{MWN_NAMESPACE}}}ResourceList")
    for idx, track in enumerate(tracks, start=1):
        resource_ref = f"A{idx}"
        resource_refs.append(resource_ref)

        sr = ET.SubElement(resource_list, f"{{{MWN_NAMESPACE}}}SoundRecording")
        sr_ref = ET.SubElement(sr, f"{{{MWN_NAMESPACE}}}ResourceReference")
        sr_ref.text = resource_ref

        sr_id = ET.SubElement(sr, f"{{{MWN_NAMESPACE}}}SoundRecordingId")
        if track.get("isrc"):
            isrc_node = ET.SubElement(sr_id, f"{{{MWN_NAMESPACE}}}ISRC")
            isrc_node.text = track["isrc"]
        prop = ET.SubElement(sr_id, f"{{{MWN_NAMESPACE}}}ProprietaryId")
        prop.set("Namespace", MWN_PROPRIETARY_NAMESPACE)
        prop.text = str(track.get("track_id") or f"{release.get('id')}-A{idx}")

        title = ET.SubElement(sr, f"{{{MWN_NAMESPACE}}}Title")
        title_text = ET.SubElement(title, f"{{{MWN_NAMESPACE}}}TitleText")
        title_text.text = track.get("title") or release.get("title") or "Unknown"

        work_ref_list = ET.SubElement(
            sr, f"{{{MWN_NAMESPACE}}}ResourceMusicalWorkReferenceList"
        )
        work_ref_item = ET.SubElement(
            work_ref_list, f"{{{MWN_NAMESPACE}}}ResourceMusicalWorkReference"
        )
        work_ref_value = ET.SubElement(
            work_ref_item, f"{{{MWN_NAMESPACE}}}ResourceMusicalWorkReference"
        )
        work_ref_value.text = work_ref

    return resource_refs


def _add_release_list(root: ET.Element, release: dict, resource_refs: list[str]) -> None:
    if not resource_refs:
        return

    release_list = ET.SubElement(root, f"{{{MWN_NAMESPACE}}}ReleaseList")
    rel = ET.SubElement(release_list, f"{{{MWN_NAMESPACE}}}Release")

    rel_ref = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}ReleaseReference")
    rel_ref.text = "R1"

    rel_type = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}ReleaseType")
    rel_type.text = _map_release_type(release.get("release_type"))

    rel_id = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}ReleaseId")
    upc = release.get("upc")
    if upc:
        icpn = ET.SubElement(rel_id, f"{{{MWN_NAMESPACE}}}ICPN")
        icpn.text = str(upc).strip()
    rel_prop = ET.SubElement(rel_id, f"{{{MWN_NAMESPACE}}}ProprietaryId")
    rel_prop.set("Namespace", MWN_PROPRIETARY_NAMESPACE)
    rel_prop.text = str(release.get("id") or uuid.uuid4().hex)

    title = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}Title")
    title_text = ET.SubElement(title, f"{{{MWN_NAMESPACE}}}TitleText")
    title_text.text = release.get("title") or "Untitled"

    res_ref_list = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}ReleaseResourceReferenceList")
    for res_ref in resource_refs:
        res_node = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}ReleaseResourceReference")
        res_node.text = res_ref

    display_artist = ET.SubElement(rel, f"{{{MWN_NAMESPACE}}}DisplayArtistName")
    display_artist.text = (
        release.get("artist_name")
        or release.get("display_artist")
        or "Unknown"
    )


def _map_writer_role(role: Optional[str]) -> str:
    role_map = {
        "composer": "Composer",
        "lyricist": "Lyricist",
        "composer_lyricist": "ComposerLyricist",
        "writer": "ComposerLyricist",
    }
    if not role:
        return "ComposerLyricist"
    return role_map.get(role.strip().lower(), "ComposerLyricist")


def _map_release_type(release_type: Optional[str]) -> str:
    if not release_type:
        return "Album"
    text = str(release_type).strip().lower()
    if "single" in text:
        return "Single"
    if "ep" == text or "extendedplay" in text or "extended play" in text:
        return "EP"
    if "album" in text:
        return "Album"
    if text in {"single", "singles"}:
        return "Single"
    if text in {"ep", "extendedplay"}:
        return "EP"
    if text in {"album"}:
        return "Album"
    return "Album"
