import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
import models  # registra todos los modelos en Base
from database import Base, SessionLocal
from routers import auth, audio, metrics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SRV — Sistema de Retroalimentacion por Voz",
    description="API para analisis de fluidez oral con IA (UPAO Taller Integrador 1)",
    version="0.2.0",
)

_allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")
_origins = ["*"] if _allowed_origin == "*" else [
    _allowed_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth.router)
app.include_router(audio.router)
app.include_router(metrics.router)


@app.on_event("startup")
def seed_textos():
    from models.session import TextoLectura
    db = SessionLocal()
    try:
        if db.query(TextoLectura).count() == 0:
            textos = [
                TextoLectura(
                    titulo="El perrito y su hueso",
                    contenido=(
                        "Habia una vez un perrito llamado Toby. "
                        "Un dia encontro un hueso grande en el parque. "
                        "Toby lo llevo a su casa muy contento. "
                        "Lo entro en el jardin para guardarlo. "
                        "Al dia siguiente volvio a buscarlo y lo encontro. "
                        "Toby meneo la cola muy feliz."
                    ),
                    nivel="1ro_primaria",
                ),
                TextoLectura(
                    titulo="El sol y la lluvia",
                    contenido=(
                        "El sol sale por las mananas y nos da luz y calor. "
                        "Las plantas crecen gracias al sol. "
                        "Cuando llueve el agua riega los campos. "
                        "Las flores beben el agua de la lluvia. "
                        "El sol y la lluvia son amigos de la naturaleza. "
                        "Debemos cuidar el agua y no desperdiciarla."
                    ),
                    nivel="1ro_primaria",
                ),
                TextoLectura(
                    titulo="Mi familia",
                    contenido=(
                        "Mi familia es muy especial para mi. "
                        "Tengo papa, mama y una hermana menor. "
                        "Por las noches cenamos todos juntos. "
                        "Mi papa me ayuda con las tareas. "
                        "Mi mama me lee cuentos antes de dormir. "
                        "Quiero mucho a mi familia."
                    ),
                    nivel="1ro_primaria",
                ),
            ]
            db.add_all(textos)
            db.commit()
    finally:
        db.close()


@app.get("/")
def health():
    return {"proyecto": "SRV - Sistema de Retroalimentacion por Voz", "estado": "Activo", "version": "0.2.0"}
