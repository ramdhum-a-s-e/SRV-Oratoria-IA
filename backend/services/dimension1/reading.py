"""
Modo Lectura — Evaluación de fidelidad (HU-28).

Compara lo que el alumno LEYÓ (transcripción) con el TEXTO original mostrado,
usando distancia de edición a nivel de palabra (Levenshtein) → WER.

  fidelidad_score: 0-100  (100 = leyó idéntico al texto)
  wer:             0-1    (Word Error Rate; menor es mejor)
"""
import re
import unicodedata


def _normalizar(texto: str) -> list[str]:
    """minúsculas, sin tildes ni puntuación → lista de palabras."""
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # quita tildes
    texto = re.sub(r"[^\w\s]", " ", texto)  # quita puntuación
    return [w for w in texto.split() if w]


def _levenshtein(ref: list[str], hyp: list[str]) -> int:
    """Distancia de edición a nivel de palabra (programación dinámica)."""
    n, m = len(ref), len(hyp)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            costo = 0 if ref[i - 1] == hyp[j - 1] else 1
            curr[j] = min(prev[j] + 1,          # eliminación
                          curr[j - 1] + 1,      # inserción
                          prev[j - 1] + costo)  # sustitución
        prev = curr
    return prev[m]


def calc_fidelidad_lectura(transcripcion: str, texto_original: str) -> dict:
    """Compara la lectura del alumno con el texto guía. Retorna fidelidad 0-100, WER y conteos."""
    ref = _normalizar(texto_original)
    hyp = _normalizar(transcripcion)

    if not ref:
        return {
            "fidelidad_score": 0.0, "wer": None,
            "palabras_texto": 0, "palabras_leidas": len(hyp),
            "nivel": "n/a", "mensaje": "No hay texto de referencia para comparar.",
        }

    distancia = _levenshtein(ref, hyp)
    wer = distancia / len(ref)
    fidelidad = round(max(0.0, 1.0 - wer) * 100, 1)

    if   fidelidad >= 90: nivel, mensaje = "excelente", "Leiste el texto casi perfecto!"
    elif fidelidad >= 70: nivel, mensaje = "bueno",     "Leiste bien, con algunos errores."
    elif fidelidad >= 50: nivel, mensaje = "regular",   "Te saltaste o cambiaste varias palabras. Sigue practicando."
    else:                 nivel, mensaje = "bajo",      "Cuesta seguir el texto. Lee despacio y con calma."

    return {
        "fidelidad_score": fidelidad,
        "wer": round(wer, 3),
        "palabras_texto": len(ref),
        "palabras_leidas": len(hyp),
        "nivel": nivel,
        "mensaje": mensaje,
    }
