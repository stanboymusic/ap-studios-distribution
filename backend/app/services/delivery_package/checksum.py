from __future__ import annotations

import hashlib
from pathlib import Path


def generate_checksum(file_path: str | Path) -> str:
    path = Path(file_path)
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
