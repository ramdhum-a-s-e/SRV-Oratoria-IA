"""Persistencia opcional del audio en Supabase Storage (Project Charter S04).

DESACTIVADA por defecto (AUDIO_PERSIST_ENABLED=0). Se decidió NO guardar la voz de
menores por ética/legalidad y por los límites del plan free; la lógica queda lista
para activarse en un entorno con consentimiento informado y un bucket privado.

Usa urllib (stdlib) para no añadir dependencias. Es defensivo: cualquier fallo se
registra y devuelve None, sin interrumpir el análisis de la sesión.
"""
import urllib.request
from loguru import logger

from config import (
    AUDIO_PERSIST_ENABLED, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_AUDIO_BUCKET,
)


def persist_audio(wav_path: str, object_name: str) -> str | None:
    """Sube el .wav a Supabase Storage y devuelve su ruta (bucket/objeto), o None.

    No hace nada si la persistencia está desactivada o faltan credenciales.
    """
    if not AUDIO_PERSIST_ENABLED:
        return None
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
        logger.warning("Persistencia activada pero falta SUPABASE_URL o SUPABASE_SERVICE_KEY")
        return None

    dest = f"{object_name}.wav"
    url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{SUPABASE_AUDIO_BUCKET}/{dest}"
    try:
        with open(wav_path, "rb") as f:
            data = f.read()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {SUPABASE_SERVICE_KEY}")
        req.add_header("apikey", SUPABASE_SERVICE_KEY)
        req.add_header("Content-Type", "audio/wav")
        req.add_header("x-upsert", "true")
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        ruta = f"{SUPABASE_AUDIO_BUCKET}/{dest}"
        logger.info(f"Audio persistido en Supabase Storage: {ruta}")
        return ruta
    except Exception as e:
        logger.warning(f"No se pudo persistir el audio ({dest}): {e}")
        return None
