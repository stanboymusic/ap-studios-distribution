from lxml import etree
from app.ddex.ern.header_builder import build_message_header
from app.ddex.ern.party_builder import build_party_list
from app.ddex.ern.resource_builder import build_resource_list
from app.ddex.ern.release_builder import build_release_list
from app.ddex.ern.deal_builder import build_deal_list
from app.ern.builder.json_parser import ErnJsonParser


def build_ern(release):
    # Ensure release_data is a dictionary for the builders
    if not isinstance(release, dict):
        # Safely extract title text
        title_attr = getattr(release, 'title', 'Unknown')
        if isinstance(title_attr, dict):
            title_text = title_attr.get('text', 'Unknown')
        else:
            title_text = str(title_attr)

        # Safely extract artist name
        artist_attr = getattr(release, 'artist', None)
        if isinstance(artist_attr, dict):
            artist_name = artist_attr.get('display_name', 'Unknown Artist')
        else:
            artist_name = str(artist_attr) if artist_attr else "Unknown Artist"

        release_data = {
            "title": {"text": title_text},
            "artist": {"display_name": artist_name},
            "tracks": getattr(release, 'tracks', []),
            "artwork": getattr(release, 'artwork', None),
            "release_type": getattr(release, 'release_type', 'Single'),
        }
    else:
        release_data = release

    tracks = release_data.get("tracks", [])
    cover_filename = release_data.get("artwork")

    root = etree.Element("NewReleaseMessage", nsmap={
        None: "http://ddex.net/xml/ern/43"
    })

    # Message Header
    build_message_header(root)

    # Party List
    artist_name = release_data.get("artist", {}).get("display_name", "Unknown Artist")
    build_party_list(root, artist_name)

    # Resource List
    build_resource_list(root, tracks, cover_filename)

    # Release List
    build_release_list(root, release_data, tracks, cover_filename is not None)

    # Deal List
    build_deal_list(root)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")