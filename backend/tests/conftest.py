"""
Configuración de pruebas de integración.

- BD de test aislada en un SQLite temporal (NUNCA toca Supabase).
- Mock del pipeline pesado (audio + Whisper) en /audio/analizar.
- D2 forzado a fallback (sin cargar spaCy/BETO ni red) para tests rápidos y deterministas.
"""
import os
import tempfile

# Aislar el entorno ANTES de importar la app (config lee estas variables al cargar).
_TMP_DB = os.path.join(tempfile.gettempdir(), "srv_pytest.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ.setdefault("JWT_SECRET", "secret_de_pruebas_0123456789abcdef0123456789")

import pytest
from fastapi.testclient import TestClient

from database import Base, engine, SessionLocal
import models       # noqa: F401  (registra todos los modelos en Base)
import main         # noqa: E402
from services.dimension1 import WordToken


@pytest.fixture(autouse=True)
def _crear_tablas():
    """Tablas limpias por cada test (aislamiento)."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _sin_modelos_nlp(monkeypatch):
    """Fuerza el fallback de D2 (regex/Jaccard) para no cargar spaCy/BETO ni usar red."""
    import services.dimension2.lexical as lex
    monkeypatch.setattr(lex, "get_spacy", lambda: None)
    monkeypatch.setattr(lex, "beto_embedding", lambda *a, **k: None)


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def db_session():
    """Sesión directa a la BD de test (para insertar datos de apoyo, p. ej. textos)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(client):
    """Registra un alumno y devuelve el header Authorization con el token."""
    client.post("/auth/register", json={
        "nombre": "Ana", "apellido": "Perez", "username": "ana_test",
        "password": "clave12345", "grado": "1", "seccion": "A",
    })
    r = client.post("/auth/login", json={"username": "ana_test", "password": "clave12345"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def mock_pipeline(monkeypatch):
    """Devuelve una función para mockear el pipeline de audio con una transcripción dada."""
    def _apply(transcript="hola yo soy ana y me gusta leer cuentos"):
        import routers.audio as r
        palabras, t = [], 0.0
        for w in transcript.split():
            palabras.append(WordToken(w, t, t + 0.3)); t += 0.4
        monkeypatch.setattr(r, "to_wav", lambda a, b: None)
        monkeypatch.setattr(r, "get_model_final", lambda: object())
        monkeypatch.setattr(r, "transcribe", lambda wav, model: (palabras, transcript))
        monkeypatch.setattr(r, "analyze_prosody", lambda wav: {
            "f0_mean_hz": 210.0, "f0_std_hz": 45.0, "jitter_pct": 1.2,
            "shimmer_db": 0.8, "hnr_db": 18.0, "intensity_mean_db": 62.0,
        })
        return transcript
    return _apply
