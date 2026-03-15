import json
import os
from pathlib import Path
from typing import List
from app.models.release import ReleaseDraft
from app.core.paths import storage_path

STORAGE_PATH = storage_path("releases")

class PersistenceService:
    @staticmethod
    def ensure_storage():
        STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_release(release: ReleaseDraft):
        PersistenceService.ensure_storage()
        file_path = STORAGE_PATH / f"{release.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(release.to_dict(), f, indent=4)

    @staticmethod
    def load_all_releases() -> List[ReleaseDraft]:
        PersistenceService.ensure_storage()
        releases = []
        for file in STORAGE_PATH.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    releases.append(ReleaseDraft.from_dict(data))
            except Exception as e:
                print(f"Error loading release {file}: {e}")
        return releases

    @staticmethod
    def delete_release(release_id: str):
        file_path = STORAGE_PATH / f"{release_id}.json"
        if file_path.exists():
            file_path.unlink()
