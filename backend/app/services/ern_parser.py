from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from lxml import etree

from app.core.paths import tenant_path


def _text(node: etree._Element | None, xpath: str) -> str | None:
    if node is None:
        return None
    value = node.findtext(xpath, default=None)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _extract_release(node: etree._Element) -> Dict[str, Any]:
    return {
        "reference": _text(node, "ReleaseReference"),
        "title": _text(node, "ReferenceTitle/TitleText")
        or _text(node, "DisplayTitleText")
        or _text(node, "Title"),
        "display_artist": _text(node, "DisplayArtistName")
        or _text(node, "DisplayArtist/PartyName/FullName"),
        "grid": _text(node, "ReleaseId/GRid"),
        "icpn": _text(node, "ReleaseId/ICPN"),
        "release_type": _text(node, "ReleaseType"),
    }


def _extract_resource(node: etree._Element) -> Dict[str, Any]:
    tag = etree.QName(node).localname
    return {
        "type": tag,
        "reference": _text(node, "ResourceReference"),
        "title": _text(node, "ReferenceTitle/TitleText")
        or _text(node, "DisplayTitleText")
        or _text(node, "Title"),
        "isrc": _text(node, "SoundRecordingId/ISRC"),
        "duration": _text(node, "Duration"),
    }


def _extract_deal(node: etree._Element) -> Dict[str, Any]:
    territories: List[str] = []
    for territory in node.findall(".//TerritoryCode"):
        value = territory.text.strip() if territory.text else ""
        if value:
            territories.append(value)

    usages: List[str] = []
    for usage in node.findall(".//UseType"):
        value = usage.text.strip() if usage.text else ""
        if value:
            usages.append(value)

    commercial_models: List[str] = []
    for model in node.findall(".//CommercialModelType"):
        value = model.text.strip() if model.text else ""
        if value:
            commercial_models.append(value)

    return {
        "release_reference": _text(node, "DealReleaseReference"),
        "territories": territories,
        "usage_types": usages,
        "commercial_models": commercial_models,
        "start_date": _text(node, ".//StartDate"),
        "end_date": _text(node, ".//EndDate"),
    }


def parse_xml_to_json(xml_bytes: bytes) -> Dict[str, Any]:
    try:
        # Optional external parser integration; fallback to built-in canonical parser.
        from ddex_python_parser import parse_ern  # type: ignore

        parsed = parse_ern(xml_bytes)
        if isinstance(parsed, dict):
            return {
                "source": "ddex_python_parser",
                "data": parsed,
            }
    except Exception:
        pass

    root = etree.fromstring(xml_bytes)
    ns = root.nsmap.get(None)

    if ns:
        # Strip namespaces for predictable local XPath handling.
        xml_no_ns = etree.fromstring(xml_bytes)
        for elem in xml_no_ns.getiterator():
            if isinstance(elem.tag, str) and "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]
        root = xml_no_ns

    message_header = root.find("MessageHeader")
    releases = [_extract_release(n) for n in root.findall(".//Release")]
    resources = [
        _extract_resource(n)
        for n in root.findall(".//SoundRecording") + root.findall(".//Image")
    ]
    deals = [_extract_deal(n) for n in root.findall(".//Deal")]

    return {
        "source": "builtin_lxml",
        "message": {
            "message_type": etree.QName(root).localname,
            "message_id": _text(message_header, "MessageId"),
            "created_at": _text(message_header, "MessageCreatedDateTime"),
            "namespace": ns,
        },
        "releases": releases,
        "resources": resources,
        "deals": deals,
        "statistics": {
            "release_count": len(releases),
            "resource_count": len(resources),
            "deal_count": len(deals),
        },
    }


def persist_parsed_release(release_id: str, tenant_id: str, parsed_payload: Dict[str, Any]) -> str:
    base = tenant_path(tenant_id, "validation", release_id)
    base.mkdir(parents=True, exist_ok=True)
    target = base / "parsed-latest.json"
    target.write_text(json.dumps(parsed_payload, indent=2), encoding="utf-8")
    return str(target)


def parse_and_persist_file(xml_path: str | Path, release_id: str, tenant_id: str) -> Dict[str, Any]:
    path = Path(xml_path)
    payload = parse_xml_to_json(path.read_bytes())
    persist_parsed_release(release_id=release_id, tenant_id=tenant_id, parsed_payload=payload)
    return payload
