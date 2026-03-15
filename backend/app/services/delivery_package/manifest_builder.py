from __future__ import annotations

from pathlib import Path
from typing import Iterable

from lxml import etree

from app.services.delivery_package.checksum import generate_checksum


def _asset_item(root: etree._Element, asset_type: str, path: Path, relative_name: str) -> None:
    item = etree.SubElement(root, "Asset")
    etree.SubElement(item, "Type").text = asset_type
    etree.SubElement(item, "FileName").text = relative_name
    etree.SubElement(item, "ChecksumAlgorithm").text = "SHA256"
    etree.SubElement(item, "Checksum").text = generate_checksum(path)


def build_manifest(assets: dict) -> bytes:
    root = etree.Element("DeliveryManifest")

    ern_path: Path = assets["ern"]
    _asset_item(root, "ERN", ern_path, "ERN.xml")

    for audio in assets.get("audio", []):
        audio_path = Path(audio)
        _asset_item(root, "Audio", audio_path, f"audio/{audio_path.name}")

    artwork = assets.get("artwork")
    if artwork:
        image_path = Path(artwork)
        _asset_item(root, "Image", image_path, f"artwork/{image_path.name}")

    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def build_checksums_lines(assets: dict) -> list[str]:
    lines: list[str] = []
    ern_path: Path = assets["ern"]
    lines.append(f"ERN.xml SHA256 {generate_checksum(ern_path)}")

    for audio in assets.get("audio", []):
        audio_path = Path(audio)
        lines.append(f"audio/{audio_path.name} SHA256 {generate_checksum(audio_path)}")

    artwork = assets.get("artwork")
    if artwork:
        image_path = Path(artwork)
        lines.append(f"artwork/{image_path.name} SHA256 {generate_checksum(image_path)}")

    return lines
