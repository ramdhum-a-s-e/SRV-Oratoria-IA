import os
from dotenv import load_dotenv

load_dotenv()

# ── Whisper ───────────────────────────────────────────────────────────────────
# "small" cabe en los 512 MB de Railway Starter; "medium" requiere ~1.5 GB.
# build.sh y este config deben usar el mismo modelo → ambos leen WHISPER_MODEL_FINAL.
WHISPER_DEVICE       = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_MODEL_LIVE   = os.getenv("WHISPER_MODEL_LIVE", "small")
WHISPER_MODEL_FINAL  = os.getenv("WHISPER_MODEL_FINAL", "medium")  # plan Hobby 8GB; alineado con build.sh

# ── Audio ─────────────────────────────────────────────────────────────────────
# Filtros anti-ruido del aula rural (paso-alto + puerta de ruido). Charter S04.
AUDIO_FILTERS_ENABLED = os.getenv("AUDIO_FILTERS_ENABLED", "1") not in ("0", "false", "False")

# Persistencia del .wav en Supabase Storage (Charter S04). DESACTIVADA por defecto:
# por ética/legalidad (voz de menores) y por límites del plan free. La lógica existe
# y se activa con AUDIO_PERSIST_ENABLED=1 + credenciales de servicio.
AUDIO_PERSIST_ENABLED = os.getenv("AUDIO_PERSIST_ENABLED", "0") in ("1", "true", "True")
SUPABASE_URL          = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_AUDIO_BUCKET = os.getenv("SUPABASE_AUDIO_BUCKET", "audios")

# ── Base de datos ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./srv_dev.db")

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or "dev_secret" in JWT_SECRET or "CAMBIA" in JWT_SECRET:
    _is_sqlite = DATABASE_URL.startswith("sqlite")
    if not _is_sqlite:
        raise ValueError(
            "JWT_SECRET no está configurado. "
            "Genera uno con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    # En desarrollo local (SQLite) se permite un valor débil con advertencia
    JWT_SECRET = JWT_SECRET or "dev_secret_solo_para_desarrollo_local"

JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))