from lxml import etree
from datetime import datetime, date
from app.config.ddex import AP_STUDIOS_PARTY
from app.config.deals import DEFAULT_DEAL


def build_ern_xml(release: dict, tracks: list):
    root = etree.Element("NewReleaseMessage", nsmap={
        None: "http://ddex.net/xml/ern/43"
    })

    header = etree.SubElement(root, "MessageHeader")
    etree.SubElement(header, "MessageCreatedDateTime").text = datetime.utcnow().isoformat()

    add_parties(root, release.get("artist", {}).get("display_name", "Unknown Artist"))
    add_deals(root)

    rel = etree.SubElement(root, "Release")
    etree.SubElement(rel, "ReferenceTitle").text = release["title"]

    resources = etree.SubElement(root, "ResourceList")

    for track in tracks:
        sr = etree.SubElement(resources, "SoundRecording")
        etree.SubElement(sr, "ReferenceTitle").text = track["title"]
        etree.SubElement(sr, "Duration").text = str(track["duration_seconds"])

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def add_parties(root, artist_name: str):
    party_list = etree.SubElement(root, "PartyList")

    # Artist
    artist_party = etree.SubElement(party_list, "Party")
    etree.SubElement(artist_party, "PartyName").text = artist_name
    etree.SubElement(artist_party, "PartyRole").text = "MainArtist"

    # Rights Controller (AP Studios)
    rc_party = etree.SubElement(party_list, "Party")
    etree.SubElement(rc_party, "PartyId").text = AP_STUDIOS_PARTY["party_id"]
    etree.SubElement(rc_party, "PartyName").text = AP_STUDIOS_PARTY["name"]
    etree.SubElement(rc_party, "PartyRole").text = AP_STUDIOS_PARTY["role"]


def add_deals(root):
    deal_list = etree.SubElement(root, "DealList")
    deal = etree.SubElement(deal_list, "Deal")

    territory = etree.SubElement(deal, "TerritoryCode")
    territory.text = "Worldwide"

    validity = etree.SubElement(deal, "ValidityPeriod")
    etree.SubElement(validity, "StartDate").text = date.today().isoformat()

    usage = etree.SubElement(deal, "CommercialModelType")
    usage.text = "SubscriptionModel"


def add_cover_art(root, image_filename: str):
    resource_list = root.find("ResourceList")
    image = etree.SubElement(resource_list, "Image")

    etree.SubElement(image, "ImageType").text = "FrontCoverImage"
    etree.SubElement(image, "FileName").text = image_filename