from __future__ import annotations

import hashlib


def generate_fingerprint(signal, sample_rate: int, n_bands: int = 64) -> dict:
    try:
        import numpy as np
        from scipy.signal import stft
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependencies: numpy/scipy. Install backend requirements.") from exc

    _, _, zxx = stft(
        signal,
        fs=sample_rate,
        window="hann",
        nperseg=2048,
        noverlap=1536,
        padded=False,
        boundary=None,
    )
    magnitude = np.abs(zxx).astype("float32")
    if magnitude.size == 0:
        raise ValueError("Unable to compute spectral representation")

    log_spec = np.log10((magnitude ** 2) + 1e-12)
    bands = np.array_split(log_spec, n_bands, axis=0)
    vector = np.array([float(chunk.mean()) if chunk.size else 0.0 for chunk in bands], dtype="float32")

    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector = vector / norm
    quantized = np.round(vector, 6).astype("float32")

    fingerprint_hash = hashlib.sha256(quantized.tobytes()).hexdigest()
    return {
        "hash": fingerprint_hash,
        "vector": [float(v) for v in quantized.tolist()],
    }
