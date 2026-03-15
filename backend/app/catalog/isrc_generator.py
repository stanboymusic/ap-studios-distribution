from __future__ import annotations

from datetime import datetime
import re


ISRC_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$")


def normalize_isrc(value: str) -> str:
    return (value or "").replace("-", "").replace(" ", "").strip().upper()


def validate_isrc_format(value: str) -> bool:
    return bool(ISRC_PATTERN.match(normalize_isrc(value)))


def generate_isrc(country: str, registrant: str, sequence: int, year: str | None = None) -> str:
    cc = (country or "").strip().upper()
    reg = (registrant or "").strip().upper()
    yy = (year or datetime.utcnow().strftime("%y")).strip()

    if len(cc) != 2:
        raise ValueError("ISRC country code must be 2 characters")
    if len(reg) != 3:
        raise ValueError("ISRC registrant code must be 3 characters")
    if not yy.isdigit() or len(yy) != 2:
        raise ValueError("ISRC year must be two digits")
    if sequence < 1 or sequence > 99999:
        raise ValueError("ISRC sequence must be between 1 and 99999")

    serial = str(sequence).zfill(5)
    candidate = f"{cc}{reg}{yy}{serial}"
    if not validate_isrc_format(candidate):
        raise ValueError("Generated ISRC is invalid")
    return candidate
