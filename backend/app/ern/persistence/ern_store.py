import hashlib
import json
from pathlib import Path
from datetime import datetime


class ErnStore:

    def __init__(self, base_path="storage/ern/releases"):
        self.base = Path(base_path)

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def save(self, release_id: str, xml: bytes, context, validation_results=None) -> dict:
        release_dir = self.base / release_id
        release_dir.mkdir(parents=True, exist_ok=True)

        versions = sorted(
            [p for p in release_dir.iterdir() if p.is_dir() and p.name.startswith("v")],
            key=lambda p: int(p.name[1:])
        )

        version = len(versions) + 1
        vdir = release_dir / f"v{version}"
        vdir.mkdir()

        xml_hash = self._hash(xml)
        graph_hash = self._hash(context.graph_fingerprint.encode())

        (vdir / "ern.xml").write_bytes(xml)

        meta = {
            "release_id": release_id,
            "version": version,
            "hash": xml_hash,
            "source_graph_hash": graph_hash,
            "profile": context.profile,
            "ern_version": "4.3",
            "language": context.language,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "validation": validation_results
        }

        (vdir / "meta.json").write_text(json.dumps(meta, indent=2))

        latest = release_dir / "latest"
        try:
            if latest.exists() or latest.is_symlink():
                latest.unlink()
            latest.symlink_to(vdir.name)
        except OSError:
            # On Windows, symlink may require admin privileges, so copy instead
            import shutil
            if latest.exists():
                shutil.rmtree(latest)
            shutil.copytree(vdir, latest)

        return meta