from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from app.fingerprinting.audio_analyzer import analyze_audio
from app.fingerprinting.fingerprint_generator import generate_fingerprint
from app.fingerprinting.similarity_engine import compare_fingerprints
from app.models.audio_fingerprint import AudioFingerprint
from app.repositories.fingerprint_repository import get_all_fingerprints, save_fingerprint

DEFAULT_SIMILARITY_THRESHOLD = float((os.getenv("FINGERPRINT_SIMILARITY_THRESHOLD") or "0.98").strip())


def process_audio_fingerprint(
    source_id: str,
    file_path: str,
    *,
    tenant_id: str = "default",
    source_type: str = "track",
    asset_path: str | None = None,
    similarity_threshold: float | None = None,
    ignore_same_source: bool = True,
) -> dict:
    threshold = similarity_threshold if similarity_threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    analysis = analyze_audio(file_path)
    fingerprint = generate_fingerprint(analysis["signal"], analysis["sample_rate"])

    best_match = None
    best_similarity = 0.0
    for existing in get_all_fingerprints(tenant_id=tenant_id):
        if ignore_same_source and existing.source_type == source_type and existing.source_id == source_id:
            continue

        similarity = 1.0 if existing.fingerprint_hash == fingerprint["hash"] else compare_fingerprints(
            fingerprint["vector"],
            existing.fingerprint_vector,
        )
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = existing
        if similarity >= threshold:
            return {
                "duplicate": True,
                "track_id": existing.source_id,
                "source_type": existing.source_type,
                "similarity": round(similarity, 6),
                "matched_fingerprint_id": existing.id,
                "matched_asset_path": existing.asset_path,
                "fingerprint": fingerprint["hash"],
            }

    record = AudioFingerprint(
        id=str(uuid4()),
        source_type=source_type,
        source_id=source_id,
        fingerprint_hash=fingerprint["hash"],
        fingerprint_vector=fingerprint["vector"],
        duration=analysis["duration"],
        sample_rate=analysis["sample_rate"],
        asset_path=asset_path,
        created_at=datetime.utcnow(),
    )
    saved = save_fingerprint(record, tenant_id=tenant_id)
    return {
        "duplicate": False,
        "fingerprint": saved.fingerprint_hash,
        "fingerprint_id": saved.id,
        "duration": round(saved.duration, 3),
        "sample_rate": saved.sample_rate,
        "closest_similarity": round(best_similarity, 6) if best_match else 0.0,
        "closest_source_id": best_match.source_id if best_match else None,
    }
