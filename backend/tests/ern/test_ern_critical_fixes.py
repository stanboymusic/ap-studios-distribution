import re
import uuid

import pytest
from lxml import etree


def _build_header_xml() -> str:
    from app.ern.builder.serializers.message_header import build_message_header
    from app.ern.models.context import ErnContext, PartyInfo

    ns = "urn:ddex:ern:test"
    root = etree.Element(f"{{{ns}}}NewReleaseMessage", nsmap={None: ns})
    ctx = ErnContext(
        message_id="TEST-001",
        sender=PartyInfo(party_id="PA-DPIDA-202402050E-4", name="AP Studios"),
        recipient=PartyInfo(party_id="PADPIDA0000000001I", name="Recipient DSP"),
        graph_fingerprint="test",
    )
    build_message_header(root, ctx, ns)
    return etree.tostring(root, encoding="utf-8").decode("utf-8")


def _extract_text(xml: str, tag: str) -> str:
    root = etree.fromstring(xml.encode("utf-8"))
    matches = root.xpath(f"//*[local-name()='{tag}']")
    if not matches:
        return ""
    return matches[0].text or ""


# -- Test Fix #1: MessageCreatedDateTime dinamico --

def test_message_created_datetime_no_hardcodeado():
    """MessageCreatedDateTime nunca debe ser la fecha hardcodeada."""
    HARDCODED = "2026-01-02T22:52:46Z"

    result_xml = []
    for _ in range(2):
        result_xml.append(_build_header_xml())

    for xml in result_xml:
        assert HARDCODED not in xml, (
            f"Hardcoded datetime found in ERN header: {HARDCODED}"
        )


def test_message_created_datetime_formato_iso8601():
    """MessageCreatedDateTime debe seguir formato ISO 8601 UTC."""
    iso8601_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    xml = _build_header_xml()
    created = _extract_text(xml, "MessageCreatedDateTime")
    assert iso8601_pattern.match(created), f"Format wrong: {created}"


def test_message_id_es_unico():
    """Cada ERN debe tener un MessageId único."""
    ids = {_extract_text(_build_header_xml(), "MessageId") for _ in range(5)}
    assert len(ids) == 5, "MessageIds are not unique"


# -- Test Fix #2: UPC placeholder bloqueado --

def test_upc_placeholder_bloqueado():
    """UPC placeholder debe lanzar ERNBuildError."""
    from app.ern.builder.serializers.releases import validate_upc_for_ern
    from app.ern.builder.serializers.releases import ERNBuildError

    with pytest.raises(ERNBuildError, match="placeholder"):
        validate_upc_for_ern("1234567890123")


def test_upc_valido_pasa():
    """UPC real con checksum correcto debe pasar."""
    from app.ern.builder.serializers.releases import validate_upc_for_ern
    # UPC válido con checksum correcto
    assert validate_upc_for_ern("012345678905") == "012345678905"


def test_upc_none_bloqueado():
    """UPC None debe lanzar ERNBuildError."""
    from app.ern.builder.serializers.releases import validate_upc_for_ern
    from app.ern.builder.serializers.releases import ERNBuildError

    with pytest.raises(ERNBuildError):
        validate_upc_for_ern(None)


# -- Test Fix #3: ISRC placeholder bloqueado --

def test_isrc_placeholder_bloqueado():
    """ISRC placeholder debe lanzar ERNBuildError."""
    from app.ern.builder.serializers.tracks import validate_isrc_for_ern
    from app.ern.builder.serializers.releases import ERNBuildError

    with pytest.raises(ERNBuildError, match="placeholder"):
        validate_isrc_for_ern("US-ABC-00-00001", "Test Track")


def test_isrc_none_bloqueado():
    """ISRC None debe lanzar ERNBuildError."""
    from app.ern.builder.serializers.tracks import validate_isrc_for_ern
    from app.ern.builder.serializers.releases import ERNBuildError

    with pytest.raises(ERNBuildError):
        validate_isrc_for_ern(None, "Track Sin ISRC")


def test_isrc_valido_pasa():
    """ISRC real válido debe pasar."""
    from app.ern.builder.serializers.tracks import validate_isrc_for_ern

    result = validate_isrc_for_ern("USRC17607839", "Valid Track")
    assert result == "USRC17607839"


def test_isrc_longitud_incorrecta_bloqueado():
    """ISRC con longitud incorrecta debe lanzar ERNBuildError."""
    from app.ern.builder.serializers.tracks import validate_isrc_for_ern
    from app.ern.builder.serializers.releases import ERNBuildError

    with pytest.raises(ERNBuildError):
        validate_isrc_for_ern("USRC1234", "Short ISRC Track")


# -- Test script de limpieza --

def test_scan_storage_no_crash_sin_storage(tmp_path, monkeypatch):
    """El script de limpieza no crashea si no hay storage."""
    import scripts.fix_storage_placeholders as fsp
    monkeypatch.setattr(fsp, "STORAGE_ROOT", tmp_path / "nonexistent")
    fsp.scan_storage(fix_mode=False)


def test_scan_storage_detecta_upc_placeholder(tmp_path, monkeypatch):
    """El script detecta UPCs placeholder en el storage."""
    import json
    import scripts.fix_storage_placeholders as fsp

    tenant_dir = tmp_path / "default"
    tenant_dir.mkdir()
    release_file = tenant_dir / "release_test.json"
    release_file.write_text(json.dumps({
        "id": "test-001",
        "title": "Test Release",
        "upc": "1234567890123",
        "tracks": []
    }), encoding="utf-8")

    monkeypatch.setattr(fsp, "STORAGE_ROOT", tmp_path)

    fsp.scan_storage(fix_mode=False)
