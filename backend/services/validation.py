"""
Validación de contenido mínimo de una sesión antes de puntuar.

Una grabación de silencio, ruido o de muy pocos segundos NO debe puntuarse:
las dimensiones D1/D2 dan puntos "por defecto" cuando no hay datos y eso
inflaba el score (sesiones de 1-2 palabras salían como "Bueno").

Umbrales acordados: una sesión es válida solo si tiene al menos
MIN_PALABRAS palabras transcritas Y MIN_DURACION_HABLA_S segundos de habla.

Este módulo lo comparten el router (/audio/analizar), el test de regresión
y el script de diagnóstico del histórico, para que el criterio sea único.
"""

MIN_PALABRAS = 10
MIN_DURACION_HABLA_S = 5.0

MENSAJE_INVALIDA = (
    "No detectamos suficiente voz en tu grabación. "
    "Intenta de nuevo y habla un poco más, despacio y claro."
)


def es_sesion_valida(word_count: int, speech_duration_s: float) -> bool:
    """True si la grabación tiene contenido suficiente para puntuar."""
    return (
        (word_count or 0) >= MIN_PALABRAS
        and (speech_duration_s or 0.0) >= MIN_DURACION_HABLA_S
    )


def motivo_invalidez(word_count: int, speech_duration_s: float) -> str | None:
    """Devuelve un motivo legible si la sesión es inválida, o None si es válida."""
    wc = word_count or 0
    dur = speech_duration_s or 0.0
    if es_sesion_valida(wc, dur):
        return None
    faltas = []
    if wc < MIN_PALABRAS:
        faltas.append(f"{wc} palabras (mínimo {MIN_PALABRAS})")
    if dur < MIN_DURACION_HABLA_S:
        faltas.append(f"{dur:.1f}s de habla (mínimo {MIN_DURACION_HABLA_S:.0f}s)")
    return "; ".join(faltas)
