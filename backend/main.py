from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def health():
    return {"proyecto": "SRV - Sistema de Retroalimentación por Voz", "estado": "Activo"}