"""
Verifica y corrige el rol del usuario admin en el storage.
Ejecutar si admin@apstudios.io aparece como artista.

Usage: python backend/scripts/fix_admin_role.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

STORAGE = Path(__file__).resolve().parents[1] / "storage" / "users" / "default" / "users.json"
ADMIN_EMAIL = "admin@apstudios.io"


def fix():
    if not STORAGE.exists():
        print(f"[!] No users file found at {STORAGE}")
        return
    users = json.loads(STORAGE.read_text(encoding="utf-8"))
    fixed = False
    for u in users:
        if u.get("email") == ADMIN_EMAIL:
            if u.get("role") != "admin":
                print(f"[fix] {ADMIN_EMAIL} tenía role='{u['role']}' → corrigiendo a 'admin'")
                u["role"] = "admin"
                fixed = True
            else:
                print(f"[ok] {ADMIN_EMAIL} ya tiene role='admin'")
    if fixed:
        STORAGE.write_text(json.dumps(users, indent=2), encoding="utf-8")
        print("[fix] Storage actualizado.")
    print(f"\nUsuarios en storage:")
    for u in users:
        print(f"  {u['email']} → role: {u['role']}")


if __name__ == "__main__":
    fix()
