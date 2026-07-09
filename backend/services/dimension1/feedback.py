PPM_MIN = 80
PPM_MAX = 120
PPM_MUY_LENTO = 60
PPM_MUY_RAPIDO = 140
BLOQUEOS_ACEPTABLE = 1
BLOQUEOS_ALTO = 3


def _puntaje_ppm(ppm: float) -> int:
    if PPM_MIN <= ppm <= PPM_MAX:
        return 3
    if PPM_MUY_LENTO <= ppm < PPM_MIN or PPM_MAX < ppm <= PPM_MUY_RAPIDO:
        return 2
    return 1


def _puntaje_pausas(long_pauses: int) -> int:
    if long_pauses == 0:
        return 2
    if long_pauses <= BLOQUEOS_ACEPTABLE:
        return 1
    return 0


# ── Scoring CONTINUO (rampas lineales en vez de escalones) ────────────────────
# Motivo: con puntajes en escalón, una diferencia mínima (p. ej. 79.9 vs 80.1 ppm,
# o una palabra más reconocida por el ASR) cruzaba un umbral y saltaba 20 puntos.
# Con rampas, pequeñas variaciones producen pequeñas variaciones de nota: más
# estable y más justo. Pesos: velocidad 60 % / pausas 40 % (equivale al antiguo
# 3 pts / 2 pts sobre 5).
W_VELOCIDAD, W_PAUSAS = 0.60, 0.40


def _score_ppm_continuo(ppm: float) -> float:
    """0-100 suave: meseta 100 en 80-120 ppm; baja lineal a 0 en 40 y 160 ppm."""
    if PPM_MIN <= ppm <= PPM_MAX:
        return 100.0
    if ppm < PPM_MIN:
        return max(0.0, (ppm - 40) / (PPM_MIN - 40) * 100)   # 40→0, 80→100
    return max(0.0, (160 - ppm) / (160 - PPM_MAX) * 100)     # 120→100, 160→0


def _score_pausas_continuo(long_pauses: int) -> float:
    """0-100: 0 bloqueos = 100; cada bloqueo resta 25 (0→100,1→75,2→50,...)."""
    return max(0.0, 100.0 - long_pauses * 25.0)


def _estrellas_desde_score(score: float) -> int:
    """Estrellas 1-5 a partir de un score 0-100 (mismos cortes que el global)."""
    if score >= 85: return 5
    if score >= 70: return 4
    if score >= 50: return 3
    if score >= 30: return 2
    return 1


def _feedback_sin_voz() -> dict:
    """Sin palabras transcritas no hay fluidez que medir: score 0 explícito.
    (El router ya rechaza estas sesiones; esto es defensa en profundidad para
    que la dimensión nunca regale los puntos por defecto de ppm=0.)"""
    return {
        "estrellas": 1,
        "color": "red",
        "mensaje_principal": "No detectamos tu voz.",
        "detalle_velocidad": "No se escucharon palabras para medir la velocidad.",
        "detalle_pausas": "No hubo habla suficiente para analizar.",
        "consejos": ["Intenta de nuevo y habla un poco mas fuerte y claro."],
        "score_d1": 0.0,
        "_ppm_pts": 0,
        "_pausas_pts": 0,
    }


def generate_feedback(ppm_result: dict, pauses_result: dict) -> dict:
    if ppm_result.get("word_count", 0) == 0:
        return _feedback_sin_voz()

    ppm = ppm_result.get("ppm", 0)
    long_pauses = pauses_result.get("long_pauses", 0)
    total_pauses = pauses_result.get("total_pauses", 0)

    # Score continuo (nuevo). Los puntos discretos se conservan solo como
    # metadato interno para compatibilidad; ya no determinan la nota.
    ppm_pts    = _puntaje_ppm(ppm)
    pausas_pts = _puntaje_pausas(long_pauses)
    score_d1   = round(W_VELOCIDAD * _score_ppm_continuo(ppm)
                       + W_PAUSAS * _score_pausas_continuo(long_pauses), 1)
    estrellas  = _estrellas_desde_score(score_d1)

    # Mensaje principal segun velocidad
    if ppm < PPM_MUY_LENTO:
        msg_velocidad = "Hablas muy despacio. Intenta leer con mas energia."
        consejo_velocidad = "Practica leer en voz alta todos los dias para ganar velocidad."
    elif ppm < PPM_MIN:
        msg_velocidad = "Hablas un poco despacio. Casi llegas al ritmo ideal."
        consejo_velocidad = "Intenta leer un poco mas rapido la proxima vez."
    elif ppm <= PPM_MAX:
        msg_velocidad = "Hablas a una velocidad perfecta."
        consejo_velocidad = None
    elif ppm <= PPM_MUY_RAPIDO:
        msg_velocidad = "Hablas un poco rapido. Respira y ve mas despacio."
        consejo_velocidad = "Antes de leer, toma aire despacio y empieza con calma."
    else:
        msg_velocidad = "Hablas muy rapido. Es dificil entenderte."
        consejo_velocidad = "Practica leer despacio, palabra por palabra."

    # Mensaje segun bloqueos
    if long_pauses == 0:
        msg_pausas = "No te bloqueaste ni una vez. Excelente fluidez."
        consejo_pausas = None
    elif long_pauses <= BLOQUEOS_ACEPTABLE:
        msg_pausas = f"Te bloqueaste {long_pauses} vez. Sigue practicando."
        consejo_pausas = "Lee el texto varias veces antes de practicar en voz alta."
    else:
        msg_pausas = f"Te bloqueaste {long_pauses} veces. Hay que practicar mas."
        consejo_pausas = "Lee el texto muchas veces en silencio primero, luego en voz alta."

    # Mensaje principal general
    if estrellas >= 4:
        mensaje_principal = "Muy bien hecho!"
        color = "green"
    elif estrellas == 3:
        mensaje_principal = "Vas bien, sigue practicando!"
        color = "yellow"
    else:
        mensaje_principal = "Puedes mejorar, no te rindas!"
        color = "red"

    consejos = [c for c in [consejo_velocidad, consejo_pausas] if c]

    return {
        "estrellas": estrellas,
        "color": color,
        "mensaje_principal": mensaje_principal,
        "detalle_velocidad": msg_velocidad,
        "detalle_pausas": msg_pausas,
        "consejos": consejos,
        "score_d1": score_d1,
        # internos para scoring global (no se muestran en frontend)
        "_ppm_pts": ppm_pts,
        "_pausas_pts": pausas_pts,
    }
