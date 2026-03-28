"""
Script de limpieza de placeholders en releases del storage.
Detecta y reporta (NO auto-corrige) UPCs e ISRCs inválidos.
El admin decide qué hacer con cada uno.

Uso:
  python backend/scripts/fix_storage_placeholders.py          # solo reportar
  python backend/scripts/fix_storage_placeholders.py --fix    # marcar como pendientes
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "releases"

# Valores que sabemos que son placeholders inválidos
INVALID_UPCS = {
    "1234567890123",
    "000000000000",
    "123456789012",
}

INVALID_ISRC_PATTERNS = [
    "US-ABC-00",
    "US-ABC",
    "XX-XXX",
    "USABC",
]


def is_invalid_upc(upc: str | None) -> bool:
    if not upc:
        return False
    return upc.strip() in INVALID_UPCS


def is_invalid_isrc(isrc: str | None) -> bool:
    if not isrc:
        return False
    isrc = isrc.strip()
    clean = isrc.replace("-", "")
    for pattern in INVALID_ISRC_PATTERNS:
        if clean.startswith(pattern.replace("-", "")):
            return True
    # ISRC válido: CC-XXX-YY-NNNNN (12 chars sin guiones)
    if len(clean) != 12:
        return True
    return False


def scan_storage(fix_mode: bool = False):
    if not STORAGE_ROOT.exists():
        print(f"[!] Storage not found: {STORAGE_ROOT}")
        return

    issues = []

    for tenant_dir in STORAGE_ROOT.iterdir():
        if not tenant_dir.is_dir():
            continue
        for release_file in tenant_dir.rglob("*.json"):
            try:
                data = json.loads(release_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            release_id = data.get("id") or data.get("release_id", "unknown")
            title = data.get("title", "untitled")
            changed = False

            # Check UPC
            upc = data.get("upc")
            if is_invalid_upc(upc):
                issues.append(
                    {
                        "file": str(release_file),
                        "release": f"{title} ({release_id})",
                        "field": "upc",
                        "value": upc,
                    }
                )
                if fix_mode:
                    data["upc"] = None
                    data["_upc_needs_assignment"] = True
                    changed = True

            # Check ISRC en release
            isrc = data.get("isrc")
            if is_invalid_isrc(isrc):
                issues.append(
                    {
                        "file": str(release_file),
                        "release": f"{title} ({release_id})",
                        "field": "isrc",
                        "value": isrc,
                    }
                )
                if fix_mode:
                    data["isrc"] = None
                    data["_isrc_needs_assignment"] = True
                    changed = True

            # Check ISRCs en tracks
            for i, track in enumerate(data.get("tracks", [])):
                track_isrc = track.get("isrc")
                if is_invalid_isrc(track_isrc):
                    issues.append(
                        {
                            "file": str(release_file),
                            "release": f"{title} ({release_id})",
                            "field": f"tracks[{i}].isrc",
                            "value": track_isrc,
                        }
                    )
                    if fix_mode:
                        data["tracks"][i]["isrc"] = None
                        data["tracks"][i]["_isrc_needs_assignment"] = True
                        changed = True

            if fix_mode and changed:
                release_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

    # Reporte
    if not issues:
        print("[OK] No placeholder issues found in storage.")
        return

    print(f"\n{'-'*60}")
    print("  AP Studios - Storage Placeholder Report")
    print(f"{'-'*60}")
    print(f"  Found {len(issues)} issue(s):\n")

    for issue in issues:
        status = "-> CLEARED" if fix_mode else "-> NEEDS FIX"
        print(f"  [{issue['field'].upper()}] {issue['release']}")
        print(f"    Value: {issue['value']!r}  {status}")
        print(f"    File:  {issue['file']}")
        print()

    if not fix_mode:
        print("  Run with --fix to clear placeholder values.")
        print("  After fixing, reassign UPCs/ISRCs via the admin panel.")
    else:
        print("  [OK] Placeholders cleared. Fields marked as _needs_assignment=true.")
        print("  Reassign real UPCs/ISRCs from the admin panel before delivery.")

    print(f"{'-'*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan AP Studios storage for invalid UPC/ISRC placeholders"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Clear invalid values and mark as needing assignment",
    )
    args = parser.parse_args()
    scan_storage(fix_mode=args.fix)
