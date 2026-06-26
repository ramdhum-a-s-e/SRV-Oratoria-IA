"""Regresión: sesiones vacías/cortas NO deben inflar el puntaje.

Antes de este guard, una grabación de silencio daba D1=60/D2=65 y dos palabras
en un segundo daban D1=100/D2=95 ("Bueno", 4 estrellas). Aquí fijamos que:
  · sin palabras → cada dimensión da 0
  · el criterio de validez exige >= MIN_PALABRAS y >= MIN_DURACION_HABLA_S
"""
from services.dimension1.feedback import generate_feedback
from services.dimension2.feedback import generate_feedback_d2
from services.validation import (
    es_sesion_valida, motivo_invalidez, MIN_PALABRAS, MIN_DURACION_HABLA_S,
)


# ── Defensa en profundidad: entrada vacía → 0 ────────────────────────────────
def test_d1_sin_voz_es_cero():
    ppm = {"ppm": 0.0, "word_count": 0, "speech_duration_s": 0.0}
    pauses = {"total_pauses": 0, "long_pauses": 0, "avg_pause_s": 0.0}
    fb = generate_feedback(ppm, pauses)
    assert fb["score_d1"] == 0.0
    assert fb["_ppm_pts"] == 0 and fb["_pausas_pts"] == 0


def test_d2_sin_voz_es_cero():
    mul = {"muletillas_count": 0, "muletillas_tasa": 0.0, "muletillas_list": []}
    ttr = {"word_count": 0, "unique_words": 0, "ttr_score": 0.0}
    coh = {"coherencia_score": 0.80, "metodo": "n/a"}
    fb = generate_feedback_d2(mul, ttr, coh)
    assert fb["score_d2"] == 0.0


def test_d1_con_voz_real_sigue_puntuando():
    # Sesión normal: el guard NO debe afectar a sesiones válidas.
    ppm = {"ppm": 100.0, "word_count": 40, "speech_duration_s": 24.0}
    pauses = {"total_pauses": 2, "long_pauses": 0, "avg_pause_s": 0.6}
    fb = generate_feedback(ppm, pauses)
    assert fb["score_d1"] > 0


# ── Criterio de validez de sesión ────────────────────────────────────────────
def test_sesion_vacia_invalida():
    assert es_sesion_valida(0, 0.0) is False


def test_sesion_dos_palabras_invalida():
    # El caso clásico que daba "Bueno": 2 palabras en ~1s.
    assert es_sesion_valida(2, 1.0) is False
    assert motivo_invalidez(2, 1.0) is not None


def test_sesion_corta_en_duracion_invalida():
    # Suficientes palabras pero muy poco tiempo de habla.
    assert es_sesion_valida(MIN_PALABRAS, MIN_DURACION_HABLA_S - 1) is False


def test_sesion_valida_pasa():
    assert es_sesion_valida(MIN_PALABRAS, MIN_DURACION_HABLA_S) is True
    assert motivo_invalidez(MIN_PALABRAS, MIN_DURACION_HABLA_S) is None
    assert es_sesion_valida(30, 20.0) is True
