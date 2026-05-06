import os
from dotenv import load_dotenv

load_dotenv()

# ── Whisper — se adapta automáticamente al entorno ────────────────────────────
# Local (PC con GPU):    WHISPER_DEVICE=cuda, LIVE=medium, FINAL=medium
# Oracle Cloud ARM:      WHISPER_DEVICE=cpu,  LIVE=small,  FINAL=medium
WHISPER_DEVICE       = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_MODEL_LIVE   = os.getenv("WHISPER_MODEL_LIVE", "small")    # chunks en vivo
WHISPER_MODEL_FINAL  = os.getenv("WHISPER_MODEL_FINAL", "medium")  # análisis final

# ── Base de datos ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/srv_db")

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET         = os.getenv("JWT_SECRET", "dev_secret_cambia_esto_en_produccion")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))