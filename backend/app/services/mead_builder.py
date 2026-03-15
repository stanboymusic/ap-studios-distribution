"""
MEAD 1.1 message builder (Media Enrichment and Description).
Namespace: http://ddex.net/xml/mead/11
"""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

MEAD_NS = "http://ddex.net/xml/mead/11"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
MEAD_VERSION = "11"
AVS_VERSION = "3"


class MEADBuildError(Exception):
    """Raised when a MEAD message cannot be built."""


def build_mead_message(
    release: dict,
    mead_data: dict,
    sender_dpid: str,
    recipient_dpid: str,
) -> str:
    """
    Build a MEAD 1.1 XML message for a release.
    """
    if not release.get("upc"):
        raise MEADBuildError(
            f"Release {release.get('id')} has no UPC - cannot build MEAD."
        )
    if not release.get("title"):
        raise MEADBuildError(f"Release {release.get('id')} has no title")

    ET.register_namespace("mead", MEAD_NS)
    ET.register_namespace("xsi", XSI_NS)

    root = ET.Element(f"{{{MEAD_NS}}}MeadMessage")
    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{MEAD_NS} {MEAD_NS}/media-enrichment-and-description.xsd",
    )
    root.set("AvsVersionId", AVS_VERSION)
    root.set(
        "LanguageAndScriptCode",
        mead_data.get("editorial_note_language", "en"),
    )

    _add_message_header(root, sender_dpid, recipient_dpid)

    rel_info_list = ET.SubElement(root, f"{{{MEAD_NS}}}ReleaseInformationList")
    rel_info = ET.SubElement(rel_info_list, f"{{{MEAD_NS}}}ReleaseInformation")

    summary = ET.SubElement(rel_info, f"{{{MEAD_NS}}}ReleaseSummary")

    rel_id = ET.SubElement(summary, f"{{{MEAD_NS}}}ReleaseId")
    ET.SubElement(rel_id, f"{{{MEAD_NS}}}ICPN").text = release["upc"]

    display_title = ET.SubElement(summary, f"{{{MEAD_NS}}}DisplayTitle")
    title_text = ET.SubElement(display_title, f"{{{MEAD_NS}}}TitleText")
    ET.SubElement(title_text, f"{{{MEAD_NS}}}Title").text = release["title"]

    if release.get("artist_name"):
        artist_name = ET.SubElement(summary, f"{{{MEAD_NS}}}DisplayArtistName")
        ET.SubElement(artist_name, f"{{{MEAD_NS}}}n").text = release["artist_name"]

    focus_isrc = mead_data.get("focus_track_isrc")
    focus_title = mead_data.get("focus_track_title")
    if focus_isrc:
        _add_focus_track(rel_info, focus_isrc, focus_title, MEAD_NS)

    editorial_note = mead_data.get("editorial_note")
    if editorial_note:
        _add_editorial_note(
            rel_info,
            editorial_note,
            mead_data.get("editorial_note_language", "en"),
            MEAD_NS,
        )

    mood = mead_data.get("mood")
    if mood:
        mood_el = ET.SubElement(rel_info, f"{{{MEAD_NS}}}Mood")
        mood_el.text = mood

    activity = mead_data.get("activity")
    if activity:
        activity_el = ET.SubElement(rel_info, f"{{{MEAD_NS}}}Activity")
        activity_el.text = activity

    theme = mead_data.get("theme")
    if theme:
        theme_el = ET.SubElement(rel_info, f"{{{MEAD_NS}}}Theme")
        theme_el.text = theme

    genre = mead_data.get("genre")
    if genre:
        genre_el = ET.SubElement(rel_info, f"{{{MEAD_NS}}}Genre")
        genre_text = ET.SubElement(genre_el, f"{{{MEAD_NS}}}GenreText")
        genre_text.text = genre
        subgenre = mead_data.get("subgenre")
        if subgenre:
            sub_el = ET.SubElement(genre_el, f"{{{MEAD_NS}}}SubGenre")
            sub_el.text = subgenre

    lyrics_data = mead_data.get("lyrics")
    if lyrics_data and lyrics_data.get("isrc") and lyrics_data.get("text"):
        _add_sound_recording_info(root, lyrics_data, MEAD_NS)

    if hasattr(ET, "indent"):
        ET.indent(root, space="  ")

    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


def _add_message_header(root: ET.Element, sender_dpid: str, recipient_dpid: str) -> None:
    header = ET.SubElement(root, f"{{{MEAD_NS}}}MessageHeader")

    msg_id = ET.SubElement(header, f"{{{MEAD_NS}}}MessageId")
    msg_id.text = f"MEAD-{uuid.uuid4().hex[:16].upper()}"

    sender_el = ET.SubElement(header, f"{{{MEAD_NS}}}MessageSender")
    ET.SubElement(sender_el, f"{{{MEAD_NS}}}PartyId").text = sender_dpid

    recipient_el = ET.SubElement(header, f"{{{MEAD_NS}}}MessageRecipient")
    ET.SubElement(recipient_el, f"{{{MEAD_NS}}}PartyId").text = recipient_dpid

    created = ET.SubElement(header, f"{{{MEAD_NS}}}MessageCreatedDateTime")
    created.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _add_focus_track(parent: ET.Element, isrc: str, title: Optional[str], ns: str) -> None:
    focus = ET.SubElement(parent, f"{{{ns}}}FocusTrack")

    sound_ref = ET.SubElement(focus, f"{{{ns}}}FocusTrackSoundRecordingId")
    ET.SubElement(sound_ref, f"{{{ns}}}ISRC").text = isrc.strip()

    if title:
        focus_title = ET.SubElement(focus, f"{{{ns}}}FocusTrackTitle")
        title_text = ET.SubElement(focus_title, f"{{{ns}}}TitleText")
        ET.SubElement(title_text, f"{{{ns}}}Title").text = title


def _add_editorial_note(parent: ET.Element, note: str, language: str, ns: str) -> None:
    editorial = ET.SubElement(parent, f"{{{ns}}}Comment")
    editorial.set("LanguageAndScriptCode", language)
    editorial.text = note


def _add_sound_recording_info(root: ET.Element, lyrics_data: dict, ns: str) -> None:
    sr_list = ET.SubElement(root, f"{{{ns}}}SoundRecordingInformationList")
    sr_info = ET.SubElement(sr_list, f"{{{ns}}}SoundRecordingInformation")

    sr_summary = ET.SubElement(sr_info, f"{{{ns}}}SoundRecordingSummary")
    sr_id = ET.SubElement(sr_summary, f"{{{ns}}}SoundRecordingId")
    ET.SubElement(sr_id, f"{{{ns}}}ISRC").text = lyrics_data["isrc"].strip()

    lyrics_el = ET.SubElement(sr_info, f"{{{ns}}}Lyrics")
    lyrics_el.set("LanguageAndScriptCode", lyrics_data.get("language", "en"))
    lyrics_text = ET.SubElement(lyrics_el, f"{{{ns}}}LyricsText")
    lyrics_text.text = lyrics_data["text"]
