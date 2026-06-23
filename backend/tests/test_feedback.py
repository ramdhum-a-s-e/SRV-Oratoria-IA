"""Pruebas de las reglas de retroalimentación y scoring por dimensión (lógica pura)."""
from services.dimension1 import calculate_ppm, detect_pauses, generate_feedback, WordToken
from services.dimension2 import detect_muletillas, calc_ttr, calc_coherencia, generate_feedback_d2
from services.dimension3 import calc_expresividad


def _palabras(transcript):
    palabras, t = [], 0.0
    for w in transcript.split():
        palabras.append(WordToken(w, t, t + 0.3)); t += 0.4
    return palabras


def test_feedback_d1():
    pal = _palabras("hola yo soy ana y me gusta leer cuentos hoy en clase")
    fb = generate_feedback(calculate_ppm(pal), detect_pauses(pal))
    assert 1 <= fb["estrellas"] <= 5
    assert "mensaje_principal" in fb
    assert "score_d1" in fb


def test_feedback_d2_fallback():
    transcript = "el gato corre. el gato come. el perro duerme tranquilo."
    fb = generate_feedback_d2(
        detect_muletillas(transcript),
        calc_ttr(transcript),
        calc_coherencia(transcript),
    )
    assert "score_d2" in fb
    assert 1 <= fb["estrellas"] <= 5
    assert "coherencia_nivel" in fb


def test_expresividad_d3():
    prosodia = {"f0_mean_hz": 210, "f0_std_hz": 60, "hnr_db": 20, "intensity_mean_db": 62}
    r = calc_expresividad(prosodia)
    assert 0 <= r["score_d3"] <= 100
    assert 1 <= r["estrellas"] <= 5
    assert "breakdown" in r


def test_expresividad_d3_sin_datos():
    r = calc_expresividad({})
    assert "score_d3" in r
    assert "breakdown" in r
