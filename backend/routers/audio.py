import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.user import Usuario
from models.session import Sesion, TextoLectura
from models.metrics import ResultadoD1, ResultadoD2, ResultadoD3
from utils.auth import get_current_user
from utils.audio import to_wav
from services.audio_processor import get_model_final
from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody, generate_feedback, calc_fidelidad_lectura
from services.dimension2 import detect_muletillas, calc_ttr, calc_coherencia, generate_feedback_d2
from services.dimension3 import calc_expresividad
from services.scoring import calc_score_global
from schemas.audio import TextoLecturaResponse

router = APIRouter(prefix="/audio", tags=["audio"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/textos", response_model=list[TextoLecturaResponse])
def listar_textos(db: Session = Depends(get_db)):
    return db.query(TextoLectura).all()


@router.post("/analizar")
async def analizar_fluidez(
    file: UploadFile = File(...),
    modo: str = Form(default="libre"),
    texto_id: Optional[int] = Form(default=None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = uuid.uuid4().hex
    ext = os.path.splitext(file.filename or "audio")[1] or ".webm"
    raw_path = os.path.join(UPLOAD_DIR, f"{uid}_raw{ext}")
    wav_path = os.path.join(UPLOAD_DIR, f"{uid}.wav")

    with open(raw_path, "wb") as f:
        f.write(await file.read())

    try:
        to_wav(raw_path, wav_path)
        model = get_model_final()
        words, transcript = transcribe(wav_path, model)
        ppm_result     = calculate_ppm(words)
        pauses_result  = detect_pauses(words)
        prosody_result = analyze_prosody(wav_path)
    finally:
        for path in (raw_path, wav_path):
            if os.path.exists(path):
                os.remove(path)

    # ── D1 ────────────────────────────────────────────────────────────────────
    feedback_d1 = generate_feedback(ppm_result, pauses_result)

    # ── Modo Lectura: fidelidad vs texto original (HU-28) ───────────────────────
    lectura_result = None
    if modo == "lectura" and texto_id is not None:
        texto_obj = db.query(TextoLectura).filter(TextoLectura.id == texto_id).first()
        if texto_obj:
            lectura_result = calc_fidelidad_lectura(transcript, texto_obj.contenido)

    # ── D2 ────────────────────────────────────────────────────────────────────
    muletillas_result = detect_muletillas(transcript)
    ttr_result        = calc_ttr(transcript)
    coh_result        = calc_coherencia(transcript)
    feedback_d2       = generate_feedback_d2(muletillas_result, ttr_result, coh_result)

    # ── D3 ────────────────────────────────────────────────────────────────────
    feedback_d3 = calc_expresividad(prosody_result or {})

    # ── Score global ──────────────────────────────────────────────────────────
    score_global = calc_score_global(
        score_d1=feedback_d1.get("score_d1", 0.0),
        score_d2=feedback_d2.get("score_d2", 0.0),
        score_d3=feedback_d3.get("score_d3", 0.0),
    )

    # ── Guardar en DB ─────────────────────────────────────────────────────────
    sesion = Sesion(usuario_id=current_user.id, modo=modo, texto_id=texto_id)
    db.add(sesion)
    db.flush()

    p = prosody_result or {}
    fb_d1_json = {k: v for k, v in feedback_d1.items() if not k.startswith("_")}
    if lectura_result:
        fb_d1_json["lectura"] = lectura_result
    resultado_d1 = ResultadoD1(
        sesion_id         = sesion.id,
        transcripcion     = transcript,
        ppm               = ppm_result["ppm"],
        word_count        = ppm_result["word_count"],
        speech_duration_s = ppm_result["speech_duration_s"],
        total_pauses      = pauses_result["total_pauses"],
        long_pauses       = pauses_result["long_pauses"],
        avg_pause_s       = pauses_result["avg_pause_s"],
        f0_mean_hz        = p.get("f0_mean_hz"),
        f0_std_hz         = p.get("f0_std_hz"),
        jitter_pct        = p.get("jitter_pct"),
        shimmer_db        = p.get("shimmer_db"),
        hnr_db            = p.get("hnr_db"),
        intensity_mean_db = p.get("intensity_mean_db"),
        estrellas         = feedback_d1["estrellas"],
        score_d1          = feedback_d1.get("score_d1"),
        feedback_json     = fb_d1_json,
    )
    resultado_d2 = ResultadoD2(
        sesion_id        = sesion.id,
        muletillas_count = muletillas_result["muletillas_count"],
        muletillas_tasa  = muletillas_result["muletillas_tasa"],
        muletillas_tipos = muletillas_result["muletillas_list"],
        ttr_score        = ttr_result["ttr_score"],
        unique_words     = ttr_result["unique_words"],
        coherencia_score = coh_result["coherencia_score"],
        score_d2         = feedback_d2["score_d2"],
        estrellas        = feedback_d2["estrellas"],
        feedback_json    = feedback_d2,
    )
    resultado_d3 = ResultadoD3(
        sesion_id           = sesion.id,
        variacion_tonal_pts = feedback_d3["breakdown"]["variacion_tonal_pts"],
        calidad_hnr_pts     = feedback_d3["breakdown"]["calidad_hnr_pts"],
        volumen_pts         = feedback_d3["breakdown"]["volumen_pts"],
        score_d3            = feedback_d3["score_d3"],
        estrellas           = feedback_d3["estrellas"],
        feedback_json       = feedback_d3,
    )
    db.add_all([resultado_d1, resultado_d2, resultado_d3])
    db.commit()

    # ── Respuesta ─────────────────────────────────────────────────────────────
    return {
        "sesion_id":     sesion.id,
        "transcripcion": transcript,
        "ppm":    ppm_result,
        "pausas": {k: v for k, v in pauses_result.items() if k != "pauses"},
        "prosodia": prosody_result,
        "retroalimentacion": {k: v for k, v in feedback_d1.items() if not k.startswith("_")},
        "lectura": lectura_result,
        "d2": {
            **muletillas_result,
            "ttr_score":       ttr_result["ttr_score"],
            "unique_words":    ttr_result["unique_words"],
            "word_count_d2":   ttr_result["word_count"],
            "coherencia_score": coh_result["coherencia_score"],
            "coherencia_nivel": feedback_d2["coherencia_nivel"],
            "coherencia_metodo": feedback_d2["coherencia_metodo"],
            "score_d2":        feedback_d2["score_d2"],
            "estrellas":       feedback_d2["estrellas"],
            "detalle_muletillas": feedback_d2["detalle_muletillas"],
            "detalle_vocabulario": feedback_d2["detalle_vocabulario"],
            "detalle_coherencia":  feedback_d2["detalle_coherencia"],
            "consejos":        feedback_d2["consejos"],
        },
        "d3": {
            "score_d3":         feedback_d3["score_d3"],
            "estrellas":        feedback_d3["estrellas"],
            "detalle_tono":     feedback_d3["detalle_tono"],
            "detalle_calidad":  feedback_d3["detalle_calidad"],
            "detalle_volumen":  feedback_d3["detalle_volumen"],
            "breakdown":        feedback_d3["breakdown"],
        },
        "score_global": score_global,
    }
