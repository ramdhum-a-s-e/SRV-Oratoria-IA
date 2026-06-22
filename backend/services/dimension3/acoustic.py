"""
Dimensión 3 — Expresividad vocal (proxy acústico)
Usa las métricas de Praat que ya se calculan en D1 (f0_std, hnr, intensity).
No requiere modelos adicionales.

score_d3: 0-100
  · variación tonal (CV de F0)   → 0-40 pts
  · calidad de voz (HNR)         → 0-30 pts
  · volumen adecuado (intensidad)→ 0-30 pts
"""
import math


def calc_expresividad(prosodia: dict) -> dict:
    """
    prosodia: dict con f0_mean_hz, f0_std_hz, hnr_db, intensity_mean_db
    Retorna score_d3 (0-100), estrellas (1-5) y desglose.
    """
    f0_mean   = prosodia.get("f0_mean_hz")    or 0.0
    f0_std    = prosodia.get("f0_std_hz")     or 0.0
    hnr       = prosodia.get("hnr_db")        or 0.0
    intensity = prosodia.get("intensity_mean_db") or 0.0

    # ── 1. Variación tonal (0-40 pts) ─────────────────────────────────────────
    # Coeficiente de variación F0: qué tan expresivo/vivo suena el tono
    # Niños expresivos: CV ≈ 0.20-0.40.  Monotonía: CV < 0.10
    if f0_mean > 0:
        cv = f0_std / f0_mean
        # Normalizar: CV=0.35 → 40 pts, CV=0.10 → 11 pts, CV=0 → 0 pts
        variacion_pts = round(min(40.0, cv * 114.3), 1)
    else:
        variacion_pts = 0.0

    # ── 2. Calidad vocal HNR (0-30 pts) ───────────────────────────────────────
    # HNR > 20 dB = voz limpia y clara.  HNR < 5 dB = voz muy ruidosa/ronca
    if hnr > 0:
        hnr_pts = round(min(30.0, (hnr / 25.0) * 30.0), 1)
    else:
        hnr_pts = 0.0

    # ── 3. Volumen adecuado (0-30 pts) ────────────────────────────────────────
    # 55-75 dB SPL = voz proyectada de niño en aula.
    # < 45 dB = muy susurrado.  > 85 dB = gritando.
    if 55 <= intensity <= 75:
        vol_pts = 30.0
    elif 45 <= intensity < 55 or 75 < intensity <= 85:
        vol_pts = 15.0
    elif intensity > 0:
        vol_pts = 5.0
    else:
        vol_pts = 10.0  # sin datos → neutro

    score_d3 = round(variacion_pts + hnr_pts + vol_pts, 1)

    # ── Estrellas ──────────────────────────────────────────────────────────────
    if score_d3 >= 85:   estrellas = 5
    elif score_d3 >= 70: estrellas = 4
    elif score_d3 >= 50: estrellas = 3
    elif score_d3 >= 30: estrellas = 2
    else:                estrellas = 1

    # ── Mensajes ──────────────────────────────────────────────────────────────
    if variacion_pts >= 30:
        msg_tono = "Tu voz suena expresiva y animada!"
    elif variacion_pts >= 15:
        msg_tono = "Tu voz tiene algo de expresividad. Puedes animarla mas."
    else:
        msg_tono = "Tu voz suena un poco plana. Intenta variar el tono."

    if hnr_pts >= 20:
        msg_calidad = "Tu voz suena clara y limpia."
    elif hnr_pts >= 10:
        msg_calidad = "Tu voz suena bien en general."
    else:
        msg_calidad = "Tu voz tiene algo de ronquera. Hidratate antes de hablar."

    if vol_pts == 30:
        msg_volumen = "Hablas con un volumen perfecto para el salon."
    elif intensity < 45:
        msg_volumen = "Hablas muy suave. Sube un poco la voz."
    elif intensity > 85:
        msg_volumen = "Hablas muy fuerte. Trata de hablar con calma."
    else:
        msg_volumen = "Tu volumen esta casi bien."

    return {
        "score_d3":    score_d3,
        "estrellas":   estrellas,
        "detalle_tono":     msg_tono,
        "detalle_calidad":  msg_calidad,
        "detalle_volumen":  msg_volumen,
        "breakdown": {
            "variacion_tonal_pts": variacion_pts,
            "calidad_hnr_pts":     hnr_pts,
            "volumen_pts":         vol_pts,
        },
    }
