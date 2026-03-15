import pytest
from unittest.mock import patch

from app.services import ern_importer
from app.services.ern_importer import ERNImporter, ERNParseError, detect_ern_version
from app.models.artist import Artist


SAMPLE_ERN_383 = """<?xml version="1.0" encoding="UTF-8"?>
<NewReleaseMessage xmlns="http://ddex.net/xml/ern/383" MessageSchemaVersionId="ern/383">
  <MessageHeader>
    <MessageId>MSG-TEST-383</MessageId>
    <MessageSender><PartyId>PA-DPIDA-202402050E-4</PartyId></MessageSender>
    <MessageCreatedDateTime>2026-03-15T10:00:00Z</MessageCreatedDateTime>
  </MessageHeader>
  <ReleaseList>
    <Release>
      <ReleaseId><ICPN>859000000012</ICPN></ReleaseId>
      <ReleaseType>Album</ReleaseType>
      <ReferenceTitle><TitleText>Mi Album de Prueba</TitleText></ReferenceTitle>
      <DisplayArtistName><FullName>Angel</FullName></DisplayArtistName>
      <ReleaseDate>2026-03-15</ReleaseDate>
      <LabelName>AP Studios</LabelName>
      <Genre><GenreText>Trap</GenreText></Genre>
      <TerritoryCode>Worldwide</TerritoryCode>
    </Release>
  </ReleaseList>
  <SoundRecordingList>
    <SoundRecording>
      <SoundRecordingId><ISRC>USXXX2600001</ISRC></SoundRecordingId>
      <ReferenceTitle><TitleText>Track Uno</TitleText></ReferenceTitle>
      <DisplayArtistName><FullName>Angel</FullName></DisplayArtistName>
      <SequenceNumber>1</SequenceNumber>
      <Duration>PT3M30S</Duration>
      <ParentalWarningType>Explicit</ParentalWarningType>
    </SoundRecording>
    <SoundRecording>
      <SoundRecordingId><ISRC>USXXX2600002</ISRC></SoundRecordingId>
      <ReferenceTitle><TitleText>Track Dos</TitleText></ReferenceTitle>
      <DisplayArtistName><FullName>Angel</FullName></DisplayArtistName>
      <SequenceNumber>2</SequenceNumber>
      <Duration>PT4M15S</Duration>
      <ParentalWarningType>NotExplicit</ParentalWarningType>
    </SoundRecording>
    <SoundRecording>
      <SoundRecordingId><ISRC>USXXX2600003</ISRC></SoundRecordingId>
      <ReferenceTitle><TitleText>Track Tres</TitleText></ReferenceTitle>
      <DisplayArtistName><FullName>Angel</FullName></DisplayArtistName>
      <SequenceNumber>3</SequenceNumber>
      <Duration>PT2M45S</Duration>
      <ParentalWarningType>NotExplicit</ParentalWarningType>
    </SoundRecording>
  </SoundRecordingList>
</NewReleaseMessage>"""

SAMPLE_ERN_34 = """<?xml version="1.0" encoding="UTF-8"?>
<NewReleaseMessage xmlns="urn:ern:std:ern:ernm:v34">
  <ReleaseList>
    <Release>
      <ReleaseId><ICPN>859000000012</ICPN></ReleaseId>
      <ReleaseType>Album</ReleaseType>
      <ReferenceTitle><TitleText>Test</TitleText></ReferenceTitle>
    </Release>
  </ReleaseList>
</NewReleaseMessage>"""



def test_detect_version_383():
    assert detect_ern_version(SAMPLE_ERN_383) == "3.8.3"


def test_detect_version_34():
    assert detect_ern_version(SAMPLE_ERN_34) == "3.4"


def test_detect_version_desconocido():
    bad = "<NewReleaseMessage xmlns=\"urn:ern:std:ern:ernm:unknown\" />"
    with pytest.raises(ERNParseError):
        detect_ern_version(bad)


def test_parse_no_escribe_en_db(tmp_path):
    importer = ERNImporter()
    with patch.object(ern_importer, "IMPORT_PREVIEW_DIR", tmp_path):
        with patch("app.services.ern_importer.cat_repo.create_release") as mocked:
            importer.parse(SAMPLE_ERN_383, tenant_id="default")
            mocked.assert_not_called()


def test_conflicto_isrc_parcial(tmp_path, monkeypatch):
    importer = ERNImporter()
    monkeypatch.setattr(ern_importer, "IMPORT_PREVIEW_DIR", tmp_path)

    monkeypatch.setattr(ern_importer.cat_repo, "is_upc_reserved", lambda *args, **kwargs: False)
    monkeypatch.setattr(ern_importer.cat_repo, "is_isrc_reserved", lambda _t, isrc: isrc == "USXXX2600002")
    monkeypatch.setattr(ern_importer.CatalogService, "get_releases", lambda *args, **kwargs: [])

    dummy_artist = Artist(name="Angel", type="SOLO")
    monkeypatch.setattr(ern_importer.CatalogService, "find_artist_by_name", lambda *args, **kwargs: dummy_artist)
    monkeypatch.setattr(ern_importer.CatalogService, "save_artist", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer, "claim_manual_upc", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer, "create_upc", lambda *args, **kwargs: "859000000999")
    monkeypatch.setattr(ern_importer, "claim_manual_isrc", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer.cat_repo, "create_release", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer.cat_repo, "create_track", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer.cat_repo, "delete_release", lambda *args, **kwargs: None)

    preview = importer.parse(SAMPLE_ERN_383, tenant_id="default")
    conflicts = [t for t in preview["tracks"] if t.get("conflict")]
    assert len(conflicts) == 1

    result = importer.confirm(preview["preview_id"], overrides={}, tenant_id="default")
    assert result["tracks_created"] == 2
    assert result["tracks_skipped"] == 1


def test_conflicto_upc_es_warning(tmp_path, monkeypatch):
    importer = ERNImporter()
    monkeypatch.setattr(ern_importer, "IMPORT_PREVIEW_DIR", tmp_path)

    monkeypatch.setattr(ern_importer.cat_repo, "is_upc_reserved", lambda *args, **kwargs: True)
    monkeypatch.setattr(ern_importer.cat_repo, "is_isrc_reserved", lambda *args, **kwargs: False)
    monkeypatch.setattr(ern_importer.CatalogService, "get_releases", lambda *args, **kwargs: [])

    dummy_artist = Artist(name="Angel", type="SOLO")
    monkeypatch.setattr(ern_importer.CatalogService, "find_artist_by_name", lambda *args, **kwargs: dummy_artist)
    monkeypatch.setattr(ern_importer.CatalogService, "save_artist", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer, "create_upc", lambda *args, **kwargs: "859000000999")
    monkeypatch.setattr(ern_importer, "claim_manual_upc", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer, "claim_manual_isrc", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer.cat_repo, "create_release", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer.cat_repo, "create_track", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer.cat_repo, "delete_release", lambda *args, **kwargs: None)

    preview = importer.parse(SAMPLE_ERN_383, tenant_id="default")
    assert preview["upc_conflict"] is True

    result = importer.confirm(preview["preview_id"], overrides={}, tenant_id="default")
    assert result["status"] == "imported"


def test_rollback_si_confirm_falla(tmp_path, monkeypatch):
    importer = ERNImporter()
    monkeypatch.setattr(ern_importer, "IMPORT_PREVIEW_DIR", tmp_path)

    monkeypatch.setattr(ern_importer.cat_repo, "is_upc_reserved", lambda *args, **kwargs: False)
    monkeypatch.setattr(ern_importer.cat_repo, "is_isrc_reserved", lambda *args, **kwargs: False)
    monkeypatch.setattr(ern_importer.CatalogService, "get_releases", lambda *args, **kwargs: [])

    dummy_artist = Artist(name="Angel", type="SOLO")
    monkeypatch.setattr(ern_importer.CatalogService, "find_artist_by_name", lambda *args, **kwargs: dummy_artist)
    monkeypatch.setattr(ern_importer.CatalogService, "save_artist", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer, "claim_manual_upc", lambda *args, **kwargs: None)
    monkeypatch.setattr(ern_importer, "create_upc", lambda *args, **kwargs: "859000000999")
    monkeypatch.setattr(ern_importer, "claim_manual_isrc", lambda *args, **kwargs: None)

    monkeypatch.setattr(ern_importer.cat_repo, "create_release", lambda *args, **kwargs: None)

    call_count = {"count": 0}

    def _raise_on_second(*_args, **_kwargs):
        call_count["count"] += 1
        if call_count["count"] == 2:
            raise RuntimeError("boom")
        return None

    delete_called = {"value": False}

    monkeypatch.setattr(ern_importer.cat_repo, "create_track", _raise_on_second)
    monkeypatch.setattr(
        ern_importer.cat_repo,
        "delete_release",
        lambda *args, **kwargs: delete_called.__setitem__("value", True),
    )

    preview = importer.parse(SAMPLE_ERN_383, tenant_id="default")

    with pytest.raises(RuntimeError):
        importer.confirm(preview["preview_id"], overrides={}, tenant_id="default")

    assert delete_called["value"] is True


def test_preview_guardado_y_cargado(tmp_path):
    importer = ERNImporter()
    with patch.object(ern_importer, "IMPORT_PREVIEW_DIR", tmp_path):
        preview = importer.parse(SAMPLE_ERN_383, tenant_id="default")
        loaded = importer._load_preview(preview["preview_id"], tenant_id="default")
        assert loaded["preview_id"] == preview["preview_id"]
        assert loaded["release"]["upc"] == "859000000012"
