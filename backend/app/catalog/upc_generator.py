from __future__ import annotations

import re


UPC_PATTERN = re.compile(r"^\d{12}$")


def calculate_checksum(number: str) -> str:
    if not number.isdigit():
        raise ValueError("UPC base must be numeric")
    odd_sum = sum(int(number[i]) for i in range(0, len(number), 2))
    even_sum = sum(int(number[i]) for i in range(1, len(number), 2))
    total = odd_sum * 3 + even_sum
    return str((10 - (total % 10)) % 10)


def generate_upc(prefix: str = "859", sequence: int = 1) -> str:
    clean_prefix = (prefix or "").strip()
    if not clean_prefix.isdigit():
        raise ValueError("UPC prefix must be numeric")
    if len(clean_prefix) >= 11:
        raise ValueError("UPC prefix must be shorter than 11 digits")

    serial_len = 11 - len(clean_prefix)
    max_serial = 10**serial_len - 1
    if sequence < 0 or sequence > max_serial:
        raise ValueError("UPC sequence out of range for configured prefix")

    body = f"{sequence:0{serial_len}d}"
    base = clean_prefix + body
    checksum = calculate_checksum(base)
    upc = base + checksum
    if not UPC_PATTERN.match(upc):
        raise ValueError("Generated UPC is invalid")
    return upc


def validate_upc(upc: str) -> bool:
    candidate = (upc or "").strip()
    if not UPC_PATTERN.match(candidate):
        return False
    return calculate_checksum(candidate[:-1]) == candidate[-1]
