from lxml import etree
from app.ddex.ern.header_builder import build_message_header
from app.ddex.ern.party_builder import build_party_list
from app.ddex.ern.resource_builder import build_resource_list
from app.ddex.ern.release_builder import build_release_list
from app.ddex.ern.deal_builder import build_deal_list
from app.ern.builder.json_parser import ErnJsonParser


def build_ern(release):
    tracks = release.tracks
    cover_filename = release.artwork
    root = etree.Element("NewReleaseMessage", nsmap={
        None: "http://ddex.net/xml/ern/43"
    })

    # Message Header
    build_message_header(root)

    # Party List
    artist_name = release.get("artist", {}).get("display_name", "Unknown Artist")
    build_party_list(root, artist_name)

    # Resource List
    build_resource_list(root, tracks, cover_filename)

    # Release List
    build_release_list(root, release, tracks, cover_filename is not None)

    # Deal List
    build_deal_list(root)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")