from lxml import etree

def build_party_list(root, artist_name: str):
    party_list = etree.SubElement(root, "PartyList")

    # Main Artist Party
    artist_party = etree.SubElement(party_list, "Party", PartyReference="P-ARTIST-1")
    artist_party_name = etree.SubElement(artist_party, "PartyName")
    etree.SubElement(artist_party_name, "FullName").text = artist_name

    # Rights Controller Party
    label_party = etree.SubElement(party_list, "Party", PartyReference="P-LABEL-1")
    etree.SubElement(label_party, "PartyId").text = "PA-DPIDA-202402050E-4"
    label_party_name = etree.SubElement(label_party, "PartyName")
    etree.SubElement(label_party_name, "FullName").text = "AP Studios"

    return party_list