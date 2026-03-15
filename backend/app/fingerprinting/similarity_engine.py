from __future__ import annotations


def compare_fingerprints(fp1: list[float], fp2: list[float]) -> float:
    if not fp1 or not fp2:
        return 0.0

    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency: numpy. Install backend requirements.") from exc

    a = np.array(fp1, dtype="float32")
    b = np.array(fp2, dtype="float32")
    size = min(a.size, b.size)
    if size == 0:
        return 0.0

    a = a[:size]
    b = b[:size]

    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0

    similarity = float(np.dot(a, b) / denom)
    return max(0.0, min(1.0, similarity))
