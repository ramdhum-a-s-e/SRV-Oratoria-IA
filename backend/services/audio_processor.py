"""
Orquestador del pipeline de análisis de voz.

- get_model_live()  → modelo pequeño para chunks en vivo (small/medium según entorno)
- get_model_final() → modelo grande para análisis final (medium)
- process_chunk()   → analiza un chunk de 10s durante el habla (solo D1 rápido)
- process_final()   → análisis completo al terminar (D1 + Praat)

Los modelos se cargan una sola vez (singleton) y se reutilizan en cada petición.
"""
from faster_whisper import WhisperModel
from config import (
    WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
    WHISPER_MODEL_LIVE, WHISPER_MODEL_FINAL,
)
from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody

_model_live: WhisperModel | None = None
_model_final: WhisperModel | None = None


def get_model_live() -> WhisperModel:
    global _model_live
    if _model_live is None:
        print(f"[SRV] Cargando modelo LIVE '{WHISPER_MODEL_LIVE}' en {WHISPER_DEVICE}...")
        _model_live = WhisperModel(
            WHISPER_MODEL_LIVE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
    return _model_live


def get_model_final() -> WhisperModel:
    global _model_final
    if _model_final is None:
        print(f"[SRV] Cargando modelo FINAL '{WHISPER_MODEL_FINAL}' en {WHISPER_DEVICE}...")
        _model_final = WhisperModel(
            WHISPER_MODEL_FINAL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
    return _model_final


def process_chunk(audio_path: str) -> dict:
    """Análisis rápido de un chunk de ~10s durante el habla en vivo.
    Solo ejecuta Whisper (sin Praat) para mantener baja la latencia."""
    words, transcript = transcribe(audio_path, get_model_live())
    return {
        "transcript": transcript,
        "ppm": calculate_ppm(words),
        "pauses": detect_pauses(words),
    }


def process_final(audio_path: str) -> dict:
    """Análisis completo al terminar de hablar.
    Usa el modelo medium + Praat para máxima precisión."""
    words, transcript = transcribe(audio_path, get_model_final())
    return {
        "transcript": transcript,
        "ppm": calculate_ppm(words),
        "pauses": detect_pauses(words),
        "prosody": analyze_prosody(audio_path),
    }