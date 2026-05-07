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


def generate_feedback(ppm_result: dict, pauses_result: dict) -> dict:
    ppm = ppm_result.get("ppm", 0)
    long_pauses = pauses_result.get("long_pauses", 0)
    total_pauses = pauses_result.get("total_pauses", 0)

    pts = _puntaje_ppm(ppm) + _puntaje_pausas(long_pauses)
    estrellas = max(1, min(5, pts))

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
    }
