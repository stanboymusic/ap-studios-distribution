"""
Assign owner_user_id to releases that have no owner.
Useful for legacy releases created before JWT ownership.

Usage:
  python backend/scripts/claim_orphan_releases.py --list
  python backend/scripts/claim_orphan_releases.py --assign-to admin@apstudios.io
  python backend/scripts/claim_orphan_releases.py --delete
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "releases"


def find_orphans():
    orphans = []
    if not STORAGE_ROOT.exists():
        return orphans
    for tenant_dir in STORAGE_ROOT.iterdir():
        if not tenant_dir.is_dir():
            continue
        for f in tenant_dir.rglob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if not data.get("owner_user_id"):
                    orphans.append((f, data))
            except Exception:
                continue
    return orphans


def list_orphans():
    orphans = find_orphans()
    if not orphans:
        print("No orphan releases found.")
        return
    print("\n" + "-" * 60)
    print(f"  Orphan releases (no owner_user_id): {len(orphans)}")
    print("-" * 60)
    for f, data in orphans:
        print(f"  - {data.get('title', 'untitled')} [{data.get('id','?')}]")
        print(f"    {f}")
    print("\n  Options:")
    print("  --assign-to <email>   assign to a user")
    print("  --delete              delete all orphans")
    print("-" * 60 + "\n")


def assign_to_user(email: str):
    from app.repositories.user_repository import get_by_email

    user = get_by_email(email, "default")
    if not user:
        print(f"[!] User not found: {email}")
        sys.exit(1)

    orphans = find_orphans()
    if not orphans:
        print("No orphan releases to assign.")
        return

    for f, data in orphans:
        data["owner_user_id"] = str(user.id)
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Assigned: {data.get('title', 'untitled')} -> {email}")

    print(f"\nAssigned {len(orphans)} release(s) to {email}")


def delete_orphans():
    orphans = find_orphans()
    if not orphans:
        print("No orphan releases to delete.")
        return

    confirm = input(
        f"  Delete {len(orphans)} orphan release(s)? [y/N] "
    ).strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    for f, data in orphans:
        f.unlink()
        print(f"  Deleted: {data.get('title', 'untitled')}")

    print(f"\nDeleted {len(orphans)} release(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--assign-to", type=str, metavar="EMAIL")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    if args.list or (not args.assign_to and not args.delete):
        list_orphans()
    elif args.assign_to:
        assign_to_user(args.assign_to)
    elif args.delete:
        delete_orphans()
