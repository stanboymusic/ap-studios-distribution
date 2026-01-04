from lxml import etree

def build_release_list(root, release_data: dict, tracks: list, has_cover: bool = False):
    release_list = etree.SubElement(root, "ReleaseList")

    release = etree.SubElement(release_list, "Release", ReleaseReference="R-001")
    
    # Use release_type from data if available
    r_type = release_data.get("release_type", "Album")
    if hasattr(r_type, "value"): # Handle Enum
        r_type = r_type.value
    etree.SubElement(release, "ReleaseType").text = str(r_type)

    ref_title = etree.SubElement(release, "ReferenceTitle")
    etree.SubElement(ref_title, "TitleText").text = release_data.get("title", {}).get("text", "Unknown Album")

    # Release Resource References
    resource_ref_list = etree.SubElement(release, "ReleaseResourceReferenceList")
    for i, track in enumerate(tracks):
        etree.SubElement(resource_ref_list, "ReleaseResourceReference").text = f"SR-{i+1:03d}"

    if has_cover:
        etree.SubElement(resource_ref_list, "ReleaseResourceReference").text = "IMG-001"

    # Display Artist
    display_artist = etree.SubElement(release, "DisplayArtist")
    etree.SubElement(display_artist, "PartyReference").text = "P-ARTIST-1"
    etree.SubElement(display_artist, "ArtistRole").text = "MainArtist"

    # Release Label
    etree.SubElement(release, "ReleaseLabelReference").text = "P-LABEL-1"

    return release_list