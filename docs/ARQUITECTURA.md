# Documentación de Arquitectura — SRV Oratoria

**Sistema de Retroalimentación por Voz (SRV) basado en IA**
I.E. Juan José Farfán — Lancones, Piura | UPAO 2026

---

## 1. Visión general

El SRV es una aplicación web cliente-servidor que captura la voz de un estudiante, la procesa
con modelos de inteligencia artificial y devuelve una retroalimentación formativa sobre la
fluidez oral, organizada en tres dimensiones (fluidez, vocabulario y expresividad). El
procesamiento del audio ocurre en el servidor y el audio se elimina tras el análisis (no se
almacena), por protección de datos de menores.

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React + Vite, React Router, WaveSurfer.js, Chart.js, Axios |
| Backend | Python 3.11, FastAPI, Uvicorn, SQLAlchemy |
| Base de datos | PostgreSQL (Supabase) — SQLite en desarrollo local |
| ASR (transcripción) | faster-whisper (modelo medium, CPU int8) |
| Análisis prosódico | praat-parselmouth (Praat) |
| Análisis lingüístico | spaCy (es_core_news_lg) + BETO (BERT en español) |
| IA generativa (opcional) | Anthropic Claude Haiku (HU-25, desactivable) |
| Reportes | ReportLab (PDF) |
| Despliegue | Railway (backend), Vercel (frontend), Supabase (BD) |
| Seguridad | JWT (python-jose), Argon2 (passlib), validación Pydantic |

## 3. Arquitectura de componentes

El sistema sigue una arquitectura de tres niveles:

1. **Cliente (navegador)** — SPA en React desplegada en Vercel. Captura el audio con
   WaveSurfer, gestiona la sesión con un token JWT y consume la API por HTTPS.
2. **API (servidor)** — FastAPI desplegada en Railway. Expone los endpoints, ejecuta el
   pipeline de IA y gestiona la persistencia.
3. **Base de datos** — PostgreSQL gestionado en Supabase, accedido vía SQLAlchemy a través del
   pooler (IPv4).

Servicios externos opcionales: la API de Anthropic (Claude) para los consejos generativos
(HU-25), a la que solo se envían métricas numéricas, nunca la voz ni la transcripción.

## 4. Estructura del backend

| Módulo | Responsabilidad |
|---|---|
| `main.py` | Arranque, CORS, logging, manejo global de errores, `ensure_schema()` |
| `routers/auth.py` | Registro, login y datos del usuario (JWT + Argon2) |
| `routers/audio.py` | Endpoint `/audio/analizar`: pipeline completo de IA |
| `routers/metrics.py` | Historial, panel del docente y generación de PDF |
| `services/dimension1` | Transcripción (Whisper), PPM, pausas y prosodia (Praat) |
| `services/dimension2` | Muletillas, riqueza léxica (TTR) y coherencia (BETO) |
| `services/dimension3` | Expresividad acústica (variación tonal, calidad) |
| `services/scoring.py` | Puntaje global ponderado D1+D2+D3 |
| `services/report_pdf.py` | Reporte PDF de desempeño |
| `services/ia_consejos.py` | Consejo generativo con Claude (HU-25, opcional) |
| `utils/audio.py` | Conversión a WAV 16 kHz (PyAV) + filtros anti-ruido |
| `utils/audio_filters.py` | Paso-alto Butterworth + puerta de ruido |
| `utils/audio_storage.py` | Persistencia opcional del audio (desactivada) |
| `utils/auth.py` | Tokens JWT, hashing y guarda de rol (RBAC) |

## 5. Pipeline de procesamiento de audio

Flujo del endpoint `POST /audio/analizar`:

1. El cliente envía el audio grabado (WebM/Opus) por HTTPS con su token JWT.
2. **Conversión**: PyAV transforma el audio a WAV mono 16 kHz.
3. **Filtros anti-ruido**: paso-alto Butterworth + puerta de ruido (mitiga el ruido del aula).
4. **Transcripción (D1)**: faster-whisper genera el texto con marcas de tiempo por palabra.
5. **Fluidez (D1)**: cálculo de PPM, detección de pausas/bloqueos y prosodia con Praat.
6. **Lectura**: en modo lectura, fidelidad vs. el texto original (distancia de Levenshtein).
7. **Vocabulario (D2)**: muletillas y TTR con spaCy; coherencia semántica con BETO.
8. **Expresividad (D3)**: variación tonal y calidad de voz desde los rasgos acústicos.
9. **Puntaje global**: ponderación 0.4·D1 + 0.35·D2 + 0.25·D3 (0–100) y estrellas.
10. **Consejo IA (opcional)**: si está activado, Claude redacta un consejo a partir de los
    puntajes (solo números).
11. **Persistencia**: se guardan la sesión y los resultados en la BD; el archivo de audio se
    **elimina**.
12. **Respuesta**: JSON con todas las métricas y la retroalimentación.

## 6. Modelo de datos

| Tabla | Descripción |
|---|---|
| `usuarios` | Datos del usuario, rol (alumno/docente), credencial hasheada |
| `textos_lectura` | Cuentos de lectura por nivel (sembrados al inicio) |
| `sesiones` | Cada práctica: usuario, modo, texto, fecha |
| `resultados_d1` | Fluidez: PPM, pausas, prosodia, transcripción, estrellas, `feedback_json` |
| `resultados_d2` | Vocabulario: muletillas, TTR, coherencia, score |
| `resultados_d3` | Expresividad: variación tonal, calidad, score |

Relaciones: un `usuario` tiene muchas `sesiones`; cada `sesion` tiene un `resultado` por
dimensión (1 a 1). Las migraciones de esquema se aplican con `ensure_schema()` (sin Alembic).

## 7. Seguridad

- **Autenticación**: tokens JWT firmados (HS256); contraseñas con hashing **Argon2**.
- **Autorización (RBAC)**: el rol viaja en el token; la guarda `require_docente` restringe los
  endpoints del panel docente; un alumno solo accede a sus propios datos.
- **Validación**: esquemas Pydantic validan y sanean todas las entradas (DTOs).
- **CORS**: orígenes controlados por variable de entorno.
- **Errores y trazas**: middleware de logging (loguru) y manejador global de excepciones que
  devuelve JSON limpio sin exponer trazas.
- **Datos sensibles**: no se registran contraseñas, tokens ni transcripciones; el audio no se
  persiste.

## 8. Despliegue

| Componente | Plataforma | Notas |
|---|---|---|
| Backend | Railway (Nixpacks) | `torch` CPU-only para imagen ligera; `build.sh` predescarga modelos |
| Base de datos | Supabase PostgreSQL | Conexión vía pooler (IPv4) |
| Frontend | Vercel | Variable `VITE_API_URL` apunta al backend |

Variables de entorno principales: `DATABASE_URL`, `JWT_SECRET`, `WHISPER_MODEL_FINAL`,
`AUDIO_FILTERS_ENABLED`, `AUDIO_PERSIST_ENABLED`, `IA_GENERATIVA_ENABLED`, `ANTHROPIC_API_KEY`,
`ALLOWED_ORIGIN`.

## 9. Decisiones de diseño y consideraciones éticas

- **Procesamiento local de voz** (Whisper en el servidor) en lugar de un ASR en la nube: la voz
  del menor no se envía a terceros.
- **Audio efímero**: el archivo se elimina tras el análisis; la persistencia existe pero está
  desactivada por defecto (motivos éticos y legales).
- **Retroalimentación por lotes + componente híbrido** (onda en vivo + análisis al terminar) en
  lugar de streaming en tiempo real, por las limitaciones de cómputo en CPU.
- Las desviaciones respecto al planteamiento inicial están sustentadas en el documento de
  *Justificaciones del Charter*.

---

*Documento de uso académico — Taller de Tesis, UPAO 2026.*
