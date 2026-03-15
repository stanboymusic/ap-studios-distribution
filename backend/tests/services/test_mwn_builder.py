import xml.etree.ElementTree as ET


RIGHTS_CONFIG = {
    "id": "rights-001",
    "work_title": "Mi Cancion",
    "iswc": "T-123456789-0",
    "territory": "US",
    "composers": [
        {
            "name": "Angel Composer",
            "role": "composer_lyricist",
            "ipi_name_number": "00123456789",
        }
    ],
    "publishers": [
        {
            "name": "AP Music Publishing",
            "role": "publisher",
            "ipi_name_number": "00987654321",
            "share_pct": 100.0,
            "recipient_dpid": "PADPIDA202402050E4",
        }
    ],
}

RELEASE = {
    "id": "release-001",
    "title": "Mi Album",
    "upc": "859000000012",
    "release_date": "2026-03-15",
    "isrcs": ["USXXX2600001"],
}


def test_mwn_xml_es_valido():
    from app.services.mwn_builder import build_mwn_message

    xml = build_mwn_message(
        rights_config=RIGHTS_CONFIG,
        release=RELEASE,
        sender_dpid="PADPIDA202402050E4",
        recipient_dpid="PADPIDA202402050E4",
    )
    root = ET.fromstring(xml)
    assert root.tag.endswith("MusicalWorkNotificationMessage")


def test_mwn_contiene_iswc():
    from app.services.mwn_builder import build_mwn_message

    xml = build_mwn_message(RIGHTS_CONFIG, RELEASE, "PADPIDA202402050E4", "X")
    assert "T-123456789-0" in xml


def test_mwn_contiene_upc():
    from app.services.mwn_builder import build_mwn_message

    xml = build_mwn_message(RIGHTS_CONFIG, RELEASE, "PADPIDA202402050E4", "X")
    assert "859000000012" in xml


def test_mwn_contiene_isrc():
    from app.services.mwn_builder import build_mwn_message

    xml = build_mwn_message(RIGHTS_CONFIG, RELEASE, "PADPIDA202402050E4", "X")
    assert "USXXX2600001" in xml


def test_mwn_falla_sin_upc():
    from app.services.mwn_builder import build_mwn_message, MWNBuildError

    release_sin_upc = {**RELEASE, "upc": None}
    try:
        build_mwn_message(RIGHTS_CONFIG, release_sin_upc, "PADPIDA202402050E4", "X")
        assert False, "Expected MWNBuildError"
    except MWNBuildError:
        assert True


def test_mwn_falla_sin_composers_ni_publishers():
    from app.services.mwn_builder import build_mwn_message, MWNBuildError

    rights_vacios = {**RIGHTS_CONFIG, "composers": [], "publishers": []}
    try:
        build_mwn_message(rights_vacios, RELEASE, "PADPIDA202402050E4", "X")
        assert False, "Expected MWNBuildError"
    except MWNBuildError:
        assert True


def test_mwn_store_guarda_y_lista():
    import tempfile
    from app.services.mwn_store import MWNStore

    with tempfile.TemporaryDirectory() as tmp:
        store = MWNStore(storage_base=tmp)
        record = store.save(
            tenant_id="tenant-1",
            release_id="release-001",
            rights_config_id="rights-001",
            recipient_dpid="PADPIDA202402050E4",
            xml_content="<MWN/>",
        )
        listed = store.list_by_release("tenant-1", "release-001")
        assert len(listed) == 1
        assert listed[0]["id"] == record["id"]


def test_mwn_store_actualiza_estado():
    import tempfile
    from app.services.mwn_store import MWNStore

    with tempfile.TemporaryDirectory() as tmp:
        store = MWNStore(storage_base=tmp)
        record = store.save("t1", "r1", "rc1", "dpid1", "<MWN/>")
        updated = store.update_status("t1", record["id"], "sent")
        assert updated["status"] == "sent"
        assert len(updated["delivery_attempts"]) == 1
