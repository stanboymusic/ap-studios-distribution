from __future__ import annotations

import math


def _resample_if_needed(signal, source_sr: int, target_sr: int):
    if source_sr == target_sr:
        return signal, source_sr

    try:
        from scipy.signal import resample_poly
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency: scipy. Install backend requirements.") from exc

    factor = math.gcd(source_sr, target_sr)
    up = target_sr // factor
    down = source_sr // factor
    signal = resample_poly(signal, up=up, down=down).astype("float32")
    return signal, target_sr


def analyze_audio(file_path: str, sample_rate: int = 22050) -> dict:
    try:
        import numpy as np
        import soundfile as sf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Missing dependencies: numpy/soundfile. Install backend requirements.") from exc

    signal = None
    sr = None

    try:
        raw, sr = sf.read(file_path, always_2d=True, dtype="float32")
        signal = raw.mean(axis=1)
    except Exception:
        # Fallback for formats that soundfile cannot decode in the current environment.
        try:
            import audioread
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Unable to decode audio. Install ffmpeg and audioread-compatible codecs.") from exc

        chunks = []
        with audioread.audio_open(file_path) as decoder:
            sr = int(decoder.samplerate)
            channels = int(decoder.channels)
            for frame in decoder:
                chunks.append(np.frombuffer(frame, dtype=np.int16))
        if not chunks:
            raise ValueError("Audio file is empty or unsupported")
        data = np.concatenate(chunks).astype("float32") / 32768.0
        if channels > 1:
            data = data.reshape((-1, channels)).mean(axis=1)
        signal = data

    if signal is None or signal.size == 0:
        raise ValueError("Audio file is empty or unsupported")

    signal, sr = _resample_if_needed(signal, int(sr), int(sample_rate))
    duration = float(signal.shape[0] / sr)
    return {
        "signal": signal,
        "sample_rate": int(sr),
        "duration": duration,
    }
