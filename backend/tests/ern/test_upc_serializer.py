import pytest
from lxml import etree

from app.ern.builder.serializers.releases import (
    ERNBuildError,
    build_release_list,
    validate_upc_for_ern,
)
from app.ern.models.release import Release
from app.ern.registry.reference_registry import ReferenceRegistry


def test_upc_valido():
    assert validate_upc_for_ern("012345678905", "release-1") == "012345678905"


def test_upc_con_espacios():
    assert validate_upc_for_ern("  012345678905  ", "release-1") == "012345678905"


def test_upc_longitud_incorrecta():
    with pytest.raises(ERNBuildError):
        validate_upc_for_ern("12345", "release-1")


def test_upc_checksum_incorrecto():
    with pytest.raises(ERNBuildError):
        validate_upc_for_ern("012345678900", "release-1")


def test_upc_no_numerico():
    with pytest.raises(ERNBuildError):
        validate_upc_for_ern("01234567890X", "release-1")


def _make_release(upc):
    return Release(
        internal_id="release-main",
        type="Single",
        title="Test",
        upc=upc,
        original_release_date="2026-01-01",
        resources=["res-1"],
        display_artists=["artist-1"],
        label="AP Studios",
    )


def test_serializer_sin_upc_lanza_error():
    root = etree.Element("NewReleaseMessage", nsmap={None: "http://ddex.net/xml/ern/43"})
    registry = ReferenceRegistry()
    releases = {"release-main": _make_release(None)}
    with pytest.raises(ERNBuildError):
        build_release_list(root, releases, registry, "http://ddex.net/xml/ern/43")


def test_xml_generado_contiene_upc_correcto():
    root = etree.Element("NewReleaseMessage", nsmap={None: "http://ddex.net/xml/ern/43"})
    registry = ReferenceRegistry()
    releases = {"release-main": _make_release("012345678905")}
    build_release_list(root, releases, registry, "http://ddex.net/xml/ern/43")

    icpn = root.find(".//{http://ddex.net/xml/ern/43}ICPN")
    assert icpn is not None
    assert icpn.text == "012345678905"
