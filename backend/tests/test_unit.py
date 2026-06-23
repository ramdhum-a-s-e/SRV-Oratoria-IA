"""Pruebas unitarias de lógica pura (sin app ni BD)."""
from services.scoring import calc_score_global
from services.dimension1.reading import calc_fidelidad_lectura


def test_score_global_ponderacion():
    assert calc_score_global(100, 100, 100)["score_global"] == 100.0
    assert calc_score_global(0, 0, 0)["score_global"] == 0.0
    # D1 pesa 40%
    assert calc_score_global(100, 0, 0)["score_global"] == 40.0


def test_score_global_niveles_y_estrellas():
    assert calc_score_global(100, 100, 100)["estrellas"] == 5
    assert calc_score_global(0, 0, 0)["estrellas"] == 1
    medio = calc_score_global(60, 60, 60)  # = 60
    assert medio["estrellas"] == 3
    assert medio["nivel"] == "En desarrollo"
    assert {"score_global", "estrellas", "nivel", "color", "mensaje", "scores_por_dimension"} <= medio.keys()


def test_fidelidad_identica():
    r = calc_fidelidad_lectura("el gato corre", "El gato corre.")
    assert r["fidelidad_score"] == 100.0
    assert r["nivel"] == "excelente"
    assert r["wer"] == 0.0


def test_fidelidad_con_errores():
    r = calc_fidelidad_lectura("el perro corre rapido", "el gato corre")
    assert 0 < r["fidelidad_score"] < 100
    assert r["palabras_texto"] == 3


def test_fidelidad_texto_vacio():
    r = calc_fidelidad_lectura("hola", "")
    assert r["fidelidad_score"] == 0.0
    assert r["nivel"] == "n/a"


def test_fidelidad_normaliza_tildes_y_puntuacion():
    # mismas palabras con distinta tilde/puntuación/mayúscula → 100%
    r = calc_fidelidad_lectura("El nino corrio", "El niño corrió!")
    assert r["fidelidad_score"] == 100.0
