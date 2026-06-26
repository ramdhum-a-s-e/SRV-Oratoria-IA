"""
Scoring y retroalimentación de la Dimensión 2 (Léxico y Coherencia).
score_d2: 0-100
  · muletillas  (0-40 pts)
  · TTR          (0-35 pts)
  · coherencia   (0-25 pts)
"""

# ─── Umbrales ─────────────────────────────────────────────────────────────────
MUL_EXCELENTE = 1   # 0-1 muletillas → 40 pts
MUL_BUENO     = 4   # 2-4            → 25 pts
MUL_REGULAR   = 8   # 5-8            → 10 pts
                    # 9+             →  0 pts

TTR_BUENO    = 0.50  # >0.50  → 35 pts
TTR_REGULAR  = 0.30  # >0.30  → 20 pts
                     # ≤0.30  →  5 pts

# Umbrales de coherencia según el método de cálculo:
# BETO da cosenos comprimidos en rango alto (~0.75-0.95);
# Jaccard da solapamiento de palabras en rango bajo (~0-0.4).
COH_UMBRALES = {
    "beto":    (0.86, 0.79),   # (bueno, regular)
    "jaccard": (0.35, 0.15),
    "n/a":     (0.0,  0.0),    # texto corto: no penalizar
}


def _pts_muletillas(count: int) -> int:
    if count <= MUL_EXCELENTE:  return 40
    if count <= MUL_BUENO:      return 25
    if count <= MUL_REGULAR:    return 10
    return 0


def _pts_ttr(ttr: float) -> int:
    if ttr > TTR_BUENO:    return 35
    if ttr > TTR_REGULAR:  return 20
    return 5


def _pts_coherencia(score: float, metodo: str = "jaccard") -> int:
    bueno, regular = COH_UMBRALES.get(metodo, COH_UMBRALES["jaccard"])
    if metodo == "n/a":          return 20   # texto corto → puntaje neutral
    if score > bueno:            return 25
    if score > regular:          return 15
    return 5


def score_to_stars(score: float) -> int:
    if score >= 85: return 5
    if score >= 70: return 4
    if score >= 50: return 3
    if score >= 30: return 2
    return 1


def _feedback_d2_sin_voz() -> dict:
    """Sin palabras no hay léxico ni coherencia que medir: score 0 explícito.
    Evita que 0 muletillas + coherencia neutra regalen ~65 pts a una sesión vacía."""
    return {
        "score_d2": 0.0,
        "estrellas": 1,
        "detalle_muletillas": "No hubo palabras para analizar.",
        "detalle_vocabulario": "No hubo palabras para medir tu vocabulario.",
        "detalle_coherencia": "No hubo suficiente habla para medir la coherencia.",
        "coherencia_nivel": "bajo",
        "coherencia_metodo": "n/a",
        "consejos": ["Intenta de nuevo y di al menos unas cuantas frases completas."],
        "breakdown": {"pts_muletillas": 0, "pts_ttr": 0, "pts_coherencia": 0},
    }


def generate_feedback_d2(muletillas: dict, ttr: dict, coherencia: dict) -> dict:
    if ttr.get("word_count", 0) == 0:
        return _feedback_d2_sin_voz()

    count     = muletillas.get("muletillas_count", 0)
    tasa      = muletillas.get("muletillas_tasa", 0.0)
    ttr_score = ttr.get("ttr_score", 0.0)
    coh_score = coherencia.get("coherencia_score", 0.0)
    coh_metodo = coherencia.get("metodo", "jaccard")

    pts_mul = _pts_muletillas(count)
    pts_ttr = _pts_ttr(ttr_score)
    pts_coh = _pts_coherencia(coh_score, coh_metodo)
    score_d2 = float(pts_mul + pts_ttr + pts_coh)  # 0-100
    estrellas = score_to_stars(score_d2)

    # Mensajes de muletillas
    if count == 0:
        msg_muletillas = "No usaste ninguna muletilla. Excelente!"
        consejo_mul = None
    elif count <= 3:
        tipos = ", ".join(muletillas.get("muletillas_list", []))
        msg_muletillas = f"Usaste {count} muletilla(s) ({tipos}). Casi perfecto."
        consejo_mul = "Antes de hablar, practica hacer una pausa corta en vez de decir 'este' o 'eh'."
    else:
        tipos = ", ".join(muletillas.get("muletillas_list", []))
        msg_muletillas = f"Usaste {count} muletillas ({tipos}). Hay que practicar mas."
        consejo_mul = "Graba tu voz, escuchala y nota cuando dices 'este' o 'eh'. Practica parar ahi."

    # Mensajes de TTR
    if ttr_score > TTR_BUENO:
        msg_ttr = "Usas palabras muy variadas. Tienes buen vocabulario!"
        consejo_ttr = None
    elif ttr_score > TTR_REGULAR:
        msg_ttr = "Tu vocabulario es adecuado para tu nivel."
        consejo_ttr = "Lee cuentos nuevos para conocer mas palabras."
    else:
        msg_ttr = "Repites muchas palabras. Intenta usar palabras diferentes."
        consejo_ttr = "Cada dia aprende 2 palabras nuevas y usaias cuando hables."

    # Mensajes de coherencia (según los puntos obtenidos, no el score crudo,
    # porque el rango depende del método BETO vs Jaccard)
    if pts_coh >= 25:
        nivel_coh = "bueno"
        msg_coh = "Tus ideas estan bien conectadas. Se entiende lo que dices!"
        consejo_coh = None
    elif pts_coh >= 15:
        nivel_coh = "regular"
        msg_coh = "Tus ideas tienen sentido en general."
        consejo_coh = "Intenta usar palabras como 'porque', 'entonces' o 'despues' para conectar ideas."
    else:
        nivel_coh = "bajo"
        msg_coh = "Tus ideas saltan de un tema a otro. Trata de organizarlas."
        consejo_coh = "Antes de hablar, piensa: primero digo esto, luego aquello."

    consejos = [c for c in [consejo_mul, consejo_ttr, consejo_coh] if c]

    return {
        "score_d2": score_d2,
        "estrellas": estrellas,
        "detalle_muletillas": msg_muletillas,
        "detalle_vocabulario": msg_ttr,
        "detalle_coherencia": msg_coh,
        "coherencia_nivel": nivel_coh,
        "coherencia_metodo": coh_metodo,
        "consejos": consejos,
        "breakdown": {
            "pts_muletillas": pts_mul,
            "pts_ttr": pts_ttr,
            "pts_coherencia": pts_coh,
        },
    }
