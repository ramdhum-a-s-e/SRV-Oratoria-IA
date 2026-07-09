"""Determinismo y estabilidad del scoring.

Dos bloques:
  1. Scoring continuo (puro, sin modelos): garantiza que ya NO hay "escalones"
     que hagan saltar la nota de golpe, y que las funciones son monótonas.
  2. Golden end-to-end (se salta si falta el audio de referencia o faster-whisper):
     analiza DOS veces el mismo .wav y exige resultado idéntico. Es la evidencia
     reproducible de que "mismo audio → misma nota".

Para activar el golden, coloca un audio en:
    backend/tests/fixtures/ref.wav
"""
import os
import pytest

from services.dimension1.feedback import (
    _score_ppm_continuo, _score_pausas_continuo, generate_feedback,
)
from services.dimension2.feedback import _pts_muletillas, _pts_ttr, _pts_coherencia
from services.dimension1 import calculate_ppm, detect_pauses, WordToken


# ══════════════════════════════════════════════════════════════════════════════
# 1. SCORING CONTINUO — sin saltos bruscos (siempre corre)
# ══════════════════════════════════════════════════════════════════════════════
def test_ppm_meseta_y_extremos():
    assert _score_ppm_continuo(100) == 100.0          # centro del rango ideal
    assert _score_ppm_continuo(80) == 100.0           # borde inferior ideal
    assert _score_ppm_continuo(120) == 100.0          # borde superior ideal
    assert _score_ppm_continuo(40) == 0.0             # muy lento
    assert _score_ppm_continuo(160) == 0.0            # muy rápido
    assert 0 < _score_ppm_continuo(60) < 100          # zona intermedia


def test_ppm_sin_cliff_en_umbral():
    """El bug original: 79.9 vs 80.1 ppm no debe cambiar la nota en bloque."""
    assert abs(_score_ppm_continuo(79.9) - _score_ppm_continuo(80.1)) < 1.0


def test_ppm_monotona_creciente_hasta_ideal():
    vals = [_score_ppm_continuo(p) for p in range(40, 81, 5)]
    assert vals == sorted(vals)                        # no decrece al acercarse al ideal


def test_pausas_continuo_decrece():
    assert _score_pausas_continuo(0) == 100.0
    assert _score_pausas_continuo(1) == 75.0
    assert _score_pausas_continuo(2) == 50.0
    assert _score_pausas_continuo(10) == 0.0           # recorte a 0, sin negativos


def test_muletillas_rampa_calibrada():
    # Reproduce los puntos centrales de los antiguos umbrales, pero suave.
    assert _pts_muletillas(0) == 40.0
    assert _pts_muletillas(1) == 40.0
    assert _pts_muletillas(4) == 25.0                  # antes 25
    assert _pts_muletillas(9) == 0.0                   # antes 0
    # sin cliff: 4 vs 5 muletillas difieren poco
    assert abs(_pts_muletillas(4) - _pts_muletillas(5)) <= 5.0


def test_ttr_rampa_calibrada():
    assert _pts_ttr(0.30) == 20.0
    assert _pts_ttr(0.50) == 35.0
    assert _pts_ttr(0.55) == 35.0                      # recorte a 35
    assert _pts_ttr(0.0) == 5.0                         # recorte a 5


def test_coherencia_interpola_por_metodo():
    # BETO: regular 0.79 → 15 pts, bueno 0.86 → 25 pts
    assert _pts_coherencia(0.79, "beto") == 15.0
    assert _pts_coherencia(0.86, "beto") == 25.0
    assert _pts_coherencia(0.95, "beto") == 25.0       # recorte a 25
    assert _pts_coherencia(0.50, "n/a") == 20.0        # texto corto → neutral


def test_feedback_d1_es_determinista_para_misma_entrada():
    """Misma entrada numérica → salida idéntica (función pura, sin aleatoriedad)."""
    ppm = {"ppm": 95.0, "word_count": 40, "speech_duration_s": 25.0}
    pauses = {"total_pauses": 2, "long_pauses": 1, "avg_pause_s": 0.7}
    a = generate_feedback(ppm, pauses)
    b = generate_feedback(dict(ppm), dict(pauses))
    assert a == b


# ══════════════════════════════════════════════════════════════════════════════
# 2. GOLDEN END-TO-END — mismo audio → misma transcripción y misma nota
# ══════════════════════════════════════════════════════════════════════════════
_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "ref.wav")


def _whisper_disponible() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not os.path.exists(_FIXTURE),
                    reason="Falta backend/tests/fixtures/ref.wav (audio de referencia).")
@pytest.mark.skipif(not _whisper_disponible(),
                    reason="faster-whisper no está instalado en este entorno.")
def test_golden_mismo_audio_misma_transcripcion():
    """Transcribe el MISMO audio dos veces y exige que sea idéntico.
    Depende del parche de decodificación determinista en fluency.transcribe()."""
    from services.dimension1 import transcribe
    from services.audio_processor import get_model_final

    model = get_model_final()
    _, t1 = transcribe(_FIXTURE, model)
    _, t2 = transcribe(_FIXTURE, model)
    assert t1 == t2, "La transcripción cambió entre dos corridas del mismo audio."


@pytest.mark.skipif(not os.path.exists(_FIXTURE),
                    reason="Falta backend/tests/fixtures/ref.wav (audio de referencia).")
@pytest.mark.skipif(not _whisper_disponible(),
                    reason="faster-whisper no está instalado en este entorno.")
def test_golden_mismo_audio_mismos_scores():
    """Pipeline D1 completo dos veces sobre el mismo audio → mismos números."""
    from services.dimension1 import transcribe, analyze_prosody
    from services.audio_processor import get_model_final

    model = get_model_final()

    def _analizar():
        words, _ = transcribe(_FIXTURE, model)
        return {
            "ppm": calculate_ppm(words),
            "pausas": detect_pauses(words),
            "d1": generate_feedback(calculate_ppm(words), detect_pauses(words)),
            "prosodia": analyze_prosody(_FIXTURE),
        }

    a, b = _analizar(), _analizar()
    assert a["ppm"] == b["ppm"]
    assert a["pausas"] == b["pausas"]
    assert a["d1"]["score_d1"] == b["d1"]["score_d1"]
    assert a["prosodia"] == b["prosodia"]
