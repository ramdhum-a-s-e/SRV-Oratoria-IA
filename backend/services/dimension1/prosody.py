import math

try:
    import parselmouth
    from parselmouth.praat import call
    _PRAAT_AVAILABLE = True
except ImportError:
    _PRAAT_AVAILABLE = False


def analyze_prosody(audio_path: str) -> dict | None:
    if not _PRAAT_AVAILABLE:
        return None

    snd = parselmouth.Sound(audio_path)

    # F0 (tono fundamental)
    pitch = snd.to_pitch()
    f0_mean = call(pitch, "Get mean", 0, 0, "Hertz")
    f0_std = call(pitch, "Get standard deviation", 0, 0, "Hertz")

    # Jitter y Shimmer (calidad de voz)
    pp = call(snd, "To PointProcess (periodic, cc)", 75, 500)
    jitter = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    shimmer = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    # HNR (claridad vocal — relación armónicos/ruido)
    harmonicity = call(snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
    hnr = call(harmonicity, "Get mean", 0, 0)

    # Intensidad (volumen)
    intensity = snd.to_intensity()
    intensity_mean = call(intensity, "Get mean", 0, 0, "energy")

    def _safe(val) -> float | None:
        if val is None or math.isnan(val):
            return None
        return round(val, 4)

    return {
        "f0_mean_hz": _safe(f0_mean),
        "f0_std_hz": _safe(f0_std),
        "jitter_pct": _safe(jitter * 100) if jitter and not math.isnan(jitter) else None,
        "shimmer_db": _safe(shimmer),
        "hnr_db": _safe(hnr),
        "intensity_mean_db": _safe(intensity_mean),
    }