# SRV — Sistema de Retroalimentación por Voz basado en IA

Sistema web que analiza la fluidez oral de estudiantes de primaria en tiempo real usando modelos de IA de código abierto. Desarrollado como proyecto de Taller Integrador 1 y Tesis de pregrado en la Universidad Privada Antenor Orrego (UPAO).

**Institución objetivo:** I.E. Juan José Farfán — Lancones, Piura, Perú  
**Contexto investigativo:** Cuasi-experimento con grupo control (n=49, 1° grado primaria)

---

## Dimensiones evaluadas

| Dimensión | Qué mide | Modelos |
|-----------|----------|---------|
| **D1 — Fluidez Mecánica y Prosodia** | PPM, pausas, F0, ritmo, volumen | faster-whisper + parselmouth |
| **D2 — Claridad y Coherencia** | Muletillas, TTR, coherencia semántica | spaCy `es_core_news_lg` + BETO |
| **D3 — Seguridad Emocional** | Arousal, valencia, nerviosismo | Wav2Vec2-SER + openSMILE |

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Python 3.11 |
| Base de datos | PostgreSQL + SQLAlchemy |
| Transcripción (ASR) | faster-whisper `medium` (español) |
| Análisis prosódico | parselmouth / Praat |
| NLP | spaCy `es_core_news_lg` |
| Emoción | Wav2Vec2 + openSMILE IS13-ComParE |
| Auth | JWT + Argon2 |
| Frontend | React + Tailwind CSS *(en desarrollo)* |
| Despliegue | Oracle Cloud Free Tier (ARM 4 OCPU / 24 GB) |

---

## Estructura del proyecto

```
SRV-Oratoria-IA/
├── backend/
│   ├── main.py                        # Punto de entrada FastAPI
│   ├── config.py                      # Variables de entorno
│   ├── database.py                    # Conexión SQLAlchemy
│   │
│   ├── routers/
│   │   ├── auth.py                    # Registro y login (JWT)
│   │   ├── audio.py                   # Recepción y análisis de audio
│   │   └── metrics.py                 # Historial y reportes
│   │
│   ├── services/
│   │   ├── audio_processor.py         # Orquestador del pipeline completo
│   │   ├── dimension1/
│   │   │   ├── fluency.py             # Cálculo de PPM
│   │   │   ├── pauses.py              # Detección de silencios (>0.5s)
│   │   │   └── prosody.py             # F0, jitter, shimmer, HNR (Praat)
│   │   ├── dimension2/
│   │   │   ├── lexical.py             # Muletillas, TTR, complejidad sintáctica
│   │   │   └── coherence.py           # Coherencia semántica entre oraciones
│   │   └── dimension3/
│   │       ├── emotion.py             # Clasificación de emoción (Wav2Vec2)
│   │       └── acoustic.py            # Features IS13-ComParE (openSMILE)
│   │
│   ├── models/
│   │   ├── user.py                    # Modelo de usuario/alumno
│   │   ├── session.py                 # Sesión de práctica
│   │   └── metrics.py                 # Métricas de fluidez por sesión
│   │
│   ├── schemas/
│   │   ├── auth.py                    # Pydantic: login, registro
│   │   ├── audio.py                   # Pydantic: request/response de análisis
│   │   └── metrics.py                 # Pydantic: respuesta de métricas
│   │
│   └── utils/
│       ├── auth.py                    # Generación y verificación de JWT
│       └── audio.py                   # Conversión y normalización de audio
│
├── frontend/                          # React (en desarrollo)
└── docs/                              # Arquitectura y manual de usuario
```

---

## Pipeline de análisis

```
[Audio WAV 16kHz]
       │
       ▼
[D1] faster-whisper ──► Texto + timestamps por palabra
       │                       │
       ▼                       ▼
[D1] parselmouth          [D2] spaCy + BETO
 F0, jitter, HNR           muletillas, TTR,
                            coherencia
       │
       ▼
[D3] Wav2Vec2-SER + openSMILE
 arousal, valence, dominance
       │
       ▼
[Resultado JSON] → Frontend (Dashboard + consejos)
```

---

## Instalación local

### Prerrequisitos
- Python 3.11+
- ffmpeg instalado en el sistema
- PostgreSQL corriendo localmente

```bash
# Clonar el repositorio
git clone https://github.com/ALS-12321/SRV-Oratoria-IA.git
cd SRV-Oratoria-IA/backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo spaCy
python -m spacy download es_core_news_lg

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de base de datos y JWT_SECRET

# Ejecutar
uvicorn main:app --reload
```

La API estará disponible en `http://localhost:8000`  
Documentación automática: `http://localhost:8000/docs`

---

## Variables de entorno

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/srv_db
JWT_SECRET=tu_clave_secreta_aqui
JWT_EXPIRE_MINUTES=1440
WHISPER_MODEL=medium
```

---

## Métricas objetivo (validadas en la tesis)

| Métrica | Meta | Justificación |
|---------|------|---------------|
| PPM (Palabras por Minuto) | 80–120 PPM para 1° grado | Estándar lectura oral primaria |
| WER (Word Error Rate) | < 10% | Límite para feedback válido |
| Latencia de análisis | < 2 segundos | Sincronía cognitiva alumno-sistema |
| Detección de pausas | Sensibilidad 0.5s | Identifica vacilaciones |

---

## Equipo

| Nombre | Rol |
|--------|-----|
| Anthony Lezcano Saavedra | Product Owner |
| Ramdhum Arévalo Espinoza | Scrum Master |

**Asesor:** Mg. Walter Manuel Cueva Chávez — UPAO  
**Periodo:** Abril – Diciembre 2026