import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from services.audio_processor import get_model_final
from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody, generate_feedback
from utils.audio import to_wav

app = FastAPI(
    title="SRV — Sistema de Retroalimentación por Voz",
    description="API para análisis de fluidez oral con IA (UPAO Taller Integrador 1)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def health():
    return {"proyecto": "SRV - Sistema de Retroalimentación por Voz", "estado": "Activo"}


@app.post("/analizar-fluidez")
async def analizar_fluidez(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    ext = os.path.splitext(file.filename or "audio")[1] or ".webm"
    raw_path = os.path.join(UPLOAD_DIR, f"{uid}_raw{ext}")
    wav_path = os.path.join(UPLOAD_DIR, f"{uid}.wav")

    with open(raw_path, "wb") as f:
        f.write(await file.read())

    try:
        # Convierte a WAV 16kHz mono (necesario para Praat)
        to_wav(raw_path, wav_path)

        model = get_model_final()
        words, transcript = transcribe(wav_path, model)
        ppm_result = calculate_ppm(words)
        pauses_result = detect_pauses(words)
        prosody_result = analyze_prosody(wav_path)
    finally:
        for path in (raw_path, wav_path):
            if os.path.exists(path):
                os.remove(path)

    ppm = ppm_result["ppm"]
    tag = "Normal" if 80 <= ppm <= 120 else ("Rápido" if ppm > 120 else "Lento")
    feedback = generate_feedback(ppm_result, pauses_result)

    return {
        "transcripcion": transcript,
        "ppm": ppm_result,
        "pausas": {k: v for k, v in pauses_result.items() if k != "pauses"},
        "prosodia": prosody_result,
        "retroalimentacion": feedback,
        "mensaje": f"Fluidez analizada: {ppm} PPM ({tag})",
    }
