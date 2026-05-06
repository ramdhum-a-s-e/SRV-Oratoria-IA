import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from services.audio_processor import get_model_final
from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody

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
    ext = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        model = get_model_final()
        words, transcript = transcribe(file_path, model)
        ppm_result = calculate_ppm(words)
        pauses_result = detect_pauses(words)
        prosody_result = analyze_prosody(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    ppm = ppm_result["ppm"]
    tag = "Normal" if 80 <= ppm <= 120 else ("Rápido" if ppm > 120 else "Lento")

    return {
        "transcripcion": transcript,
        "ppm": ppm_result,
        "pausas": {k: v for k, v in pauses_result.items() if k != "pauses"},
        "prosodia": prosody_result,
        "mensaje": f"Fluidez analizada: {ppm} PPM ({tag})",
    }
