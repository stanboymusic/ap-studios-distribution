import xml.etree.ElementTree as ET


RELEASE = {
    "id": "release-001",
    "title": "Mi Album",
    "upc": "859000000012",
    "artist_name": "Angel",
    "isrcs": ["USXXX2600001", "USXXX2600002"],
}

MEAD_DATA_FULL = {
    "focus_track_isrc": "USXXX2600001",
    "focus_track_title": "Mi Cancion Principal",
    "editorial_note": "Un album que fusiona trap y sonidos caribenos.",
    "editorial_note_language": "es",
    "mood": "Energetic",
    "activity": "Running",
    "theme": "Ambition",
    "genre": "Trap Latino",
    "subgenre": "Reggaeton",
    "lyrics": {
        "isrc": "USXXX2600001",
        "text": "Verso uno...",
        "language": "es",
    },
}


def parse_xml(xml_str: str) -> ET.Element:
    clean = xml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', "").strip()
    return ET.fromstring(clean)


def test_mead_xml_parseable():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "SPOTIFY-DPID")
    root = parse_xml(xml)
    assert root is not None


def test_mead_namespace_correcto():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "SPOTIFY-DPID")
    assert "http://ddex.net/xml/mead/11" in xml


def test_mead_contiene_upc():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "X")
    assert "859000000012" in xml


def test_mead_contiene_focus_track():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "X")
    assert "USXXX2600001" in xml
    assert "FocusTrack" in xml


def test_mead_contiene_editorial_note():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "X")
    assert "trap y sonidos" in xml


def test_mead_contiene_mood_y_activity():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, MEAD_DATA_FULL, "PA-DPIDA-202402050E-4", "X")
    assert "Energetic" in xml
    assert "Running" in xml


def test_mead_falla_sin_upc():
    from app.services.mead_builder import build_mead_message, MEADBuildError

    release_sin_upc = {**RELEASE, "upc": None}
    try:
        build_mead_message(release_sin_upc, {}, "PA-DPIDA-202402050E-4", "X")
        assert False, "Expected MEADBuildError"
    except MEADBuildError:
        assert True


def test_mead_minimo_solo_upc_y_titulo():
    from app.services.mead_builder import build_mead_message

    xml = build_mead_message(RELEASE, {}, "PA-DPIDA-202402050E-4", "X")
    assert "859000000012" in xml
    assert "Mi Album" in xml


def test_mead_store_ciclo_completo():
    import tempfile
    from app.services.mead_store import MEADStore

    with tempfile.TemporaryDirectory() as tmp:
        store = MEADStore(storage_base=tmp)
        record = store.save(
            tenant_id="t1",
            release_id="r1",
            recipient_dpid="SPOTIFY-DPID",
            xml_content="<MeadMessage/>",
            mead_data={"focus_track_isrc": "USXXX001"},
        )
        assert record["status"] == "pending"
        listed = store.list_by_release("t1", "r1")
        assert len(listed) == 1
        updated = store.update_status("t1", record["id"], "sent")
        assert updated["status"] == "sent"
