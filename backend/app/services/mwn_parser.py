from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from lxml import etree


@dataclass
class MWNMessage:
    release_id: Optional[str]
    status: str
    issues: List[str]
    message_id: Optional[str]
    raw_status: Optional[str]


def _strip_namespaces(root: etree._Element) -> etree._Element:
    for elem in root.getiterator():
        if isinstance(elem.tag, str) and "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
    return root


def _first_text(root: etree._Element, paths: list[str]) -> Optional[str]:
    for path in paths:
        value = root.findtext(path)
        if value and value.strip():
            return value.strip()
    return None


def _normalize_status(raw_status: Optional[str]) -> str:
    text = (raw_status or "").strip().lower()
    if text in {"accepted", "accept", "confirmed", "ok", "success"}:
        return "ACCEPTED"
    if text in {"rejected", "reject", "failed", "error"}:
        return "REJECTED"
    if text in {"processing", "in_progress", "pending"}:
        return "PROCESSING"
    return "PROCESSING"


def parse_mwn(xml_bytes: bytes) -> MWNMessage:
    root = etree.fromstring(xml_bytes)
    root = _strip_namespaces(root)

    release_id = _first_text(
        root,
        [
            ".//ReleaseId",
            ".//ReleaseReference",
            ".//ResourceReleaseId",
            ".//MessageThreadId",
            ".//CorrelationId",
        ],
    )
    raw_status = _first_text(
        root,
        [
            ".//NotificationType",
            ".//MessageStatus",
            ".//Status",
            ".//AcknowledgementStatus",
        ],
    )
    status = _normalize_status(raw_status)
    message_id = _first_text(root, [".//MessageId", ".//NotificationId"])

    issues: List[str] = []
    for path in [".//Issue", ".//Error", ".//ErrorText", ".//Description", ".//Comment"]:
        for elem in root.findall(path):
            text = (elem.text or "").strip()
            if text:
                issues.append(text)

    return MWNMessage(
        release_id=release_id,
        status=status,
        issues=issues,
        message_id=message_id,
        raw_status=raw_status,
    )
