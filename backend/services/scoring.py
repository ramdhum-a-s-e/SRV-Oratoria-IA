"""
Score global ponderado D1 + D2 + D3
  D1 Fluidez oral:         40%
  D2 Coherencia y léxico:  35%
  D3 Expresividad vocal:   25%
"""

W_D1, W_D2, W_D3 = 0.40, 0.35, 0.25


def _d1_to_score(feedback_d1: dict) -> float:
    """Convierte el resultado D1 a score 0-100 usando pts internos."""
    ppm_pts     = feedback_d1.get("_ppm_pts", 0)
    pausas_pts  = feedback_d1.get("_pausas_pts", 0)
    total_pts   = ppm_pts + pausas_pts     # 0-5
    return round((total_pts / 5.0) * 100, 1)


def calc_score_global(score_d1: float, score_d2: float, score_d3: float) -> dict:
    score = round(W_D1 * score_d1 + W_D2 * score_d2 + W_D3 * score_d3, 1)

    if score >= 85:
        nivel, color = "Sobresaliente", "green"
        mensaje = "Eres un orador excelente para tu nivel!"
    elif score >= 70:
        nivel, color = "Bueno", "green"
        mensaje = "Muy buen trabajo! Sigue practicando."
    elif score >= 50:
        nivel, color = "En desarrollo", "yellow"
        mensaje = "Vas bien! Con mas practica lo lograras."
    elif score >= 30:
        nivel, color = "Necesita apoyo", "red"
        mensaje = "No te rindas, cada practica te hace mejor."
    else:
        nivel, color = "Inicio", "red"
        mensaje = "Sigue intentandolo, lo importante es practicar."

    if score >= 85:   estrellas = 5
    elif score >= 70: estrellas = 4
    elif score >= 50: estrellas = 3
    elif score >= 30: estrellas = 2
    else:             estrellas = 1

    return {
        "score_global": score,
        "estrellas":    estrellas,
        "nivel":        nivel,
        "color":        color,
        "mensaje":      mensaje,
        "scores_por_dimension": {
            "d1": score_d1,
            "d2": score_d2,
            "d3": score_d3,
        },
    }
