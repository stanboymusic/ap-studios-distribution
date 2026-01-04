from lxml import etree

def build_resource_list(root, tracks: list, cover_filename: str = None):
    resource_list = etree.SubElement(root, "ResourceList")

    # Sound Recordings
    for i, track in enumerate(tracks):
        sr_ref = f"SR-{i+1:03d}"
        sr = etree.SubElement(resource_list, "SoundRecording", SoundRecordingReference=sr_ref)

        etree.SubElement(sr, "SoundRecordingType").text = "MusicalWorkSoundRecording"

        ref_title = etree.SubElement(sr, "ReferenceTitle")
        etree.SubElement(ref_title, "TitleText").text = track.get("title", "Unknown")

        # Duration in ISO 8601 format
        duration_seconds = track.get("duration_seconds", 180)
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_iso = f"PT{minutes}M{seconds}S"
        etree.SubElement(sr, "Duration").text = duration_iso

        # Territory details
        details = etree.SubElement(sr, "SoundRecordingDetailsByTerritory")
        etree.SubElement(details, "TerritoryCode").text = "Worldwide"

        title = etree.SubElement(details, "Title")
        etree.SubElement(title, "TitleText").text = track.get("title", "Unknown")

        display_artist = etree.SubElement(details, "DisplayArtist")
        etree.SubElement(display_artist, "PartyReference").text = "P-ARTIST-1"
        etree.SubElement(display_artist, "ArtistRole").text = "MainArtist"

        # File reference
        isrc = track.get("isrc", "UNKNOWN")
        file_element = etree.SubElement(sr, "File")
        etree.SubElement(file_element, "FileName").text = f"resources/audio/{isrc}.wav"

    # Image
    if cover_filename:
        img = etree.SubElement(resource_list, "Image", ImageReference="IMG-001")
        etree.SubElement(img, "ImageType").text = "FrontCoverImage"
        
        # File reference for Image
        file_element = etree.SubElement(img, "File")
        etree.SubElement(file_element, "FileName").text = "resources/images/cover.jpg"

    return resource_list