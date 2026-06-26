# Informe de problemas de despliegue — SRV-Oratoria-IA

**Proyecto:** SRV — Sistema de Retroalimentación por Voz basado en IA (UPAO)
**Fecha del análisis:** 22 de junio de 2026
**Entornos involucrados:** Railway (backend FastAPI), Supabase (PostgreSQL), Vercel (frontend React)
**Autor del registro:** Equipo de desarrollo (Scrum Master: Ramdhum Arévalo)

> Este documento recopila, como evidencia, los problemas encontrados durante la
> puesta en producción del backend y frontend, **antes y durante** su solución.
> Cada hallazgo incluye: causa raíz, evidencia (extracto de log), impacto y estado.

---

## Resumen ejecutivo

| # | Problema | Capa | Severidad | Estado |
|---|----------|------|-----------|--------|
| 1 | Conflicto de dependencias `huggingface_hub` | Build | 🔴 Crítica | ✅ Resuelto |
| 2 | Imagen demasiado grande (torch + CUDA inútil) | Build/Imagen | 🟠 Alta | ⏳ Pendiente |
| 3 | Conexión a BD falla por IPv6 (Network unreachable) | Runtime | 🔴 Crítica | ✅ Resuelto |
| 4 | spaCy no carga en producción (fallback a regex) | Runtime | 🟠 Alta | ⏳ Pendiente |
| 5 | Modelos degradados vs. plan (Whisper/spaCy) | Calidad | 🟡 Media | ⏳ Pendiente |
| 6 | `JWT_SECRET` expuesto como ARG/ENV en Dockerfile | Seguridad | 🟠 Alta | ⏳ Pendiente |
| 7 | `transformers` se instala dos veces (redundante) | Eficiencia | 🟡 Media | ⏳ Pendiente |
| 8 | Vercel no desplegó el commit del frontend | Deploy FE | 🟡 Media | ✅ Resuelto |

---

## 1. Conflicto de dependencias `huggingface_hub` (build falla)

- **Capa:** Build (Railway / Nixpacks / pip)
- **Severidad:** 🔴 Crítica — el build se detenía por completo.
- **Estado:** ✅ Resuelto

**Descripción.** El `pip install -r requirements.txt` abortaba con `ResolutionImpossible`
durante la instalación de dependencias.

**Causa raíz.** Se fijó `huggingface_hub==1.13.0`, pero `transformers` exige
`huggingface-hub < 1.0`. Versiones incompatibles → pip no puede resolver.

**Evidencia (log de build):**
```
ERROR: Cannot install -r requirements.txt (line 18), -r requirements.txt (line 24)
and huggingface_hub==1.13.0 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested huggingface_hub==1.13.0
    faster-whisper 1.2.1 depends on huggingface-hub>=0.21
    transformers 4.52.4 depends on huggingface-hub<1.0 and >=0.30.0

ERROR: ResolutionImpossible
Build Failed: ... pip install -r requirements.txt did not complete successfully: exit code: 1
```

**Impacto.** Ningún despliegue posible; el contenedor nunca se generaba.

**Solución aplicada.** Bajar el pin a `huggingface_hub==0.34.4` (compatible con
`transformers` `>=0.30.0,<1.0`, `faster-whisper` y spaCy) en `requirements.txt` y
`requirements-prod.txt`. Verificado con `pip install --dry-run` (sin conflictos) y
confirmado en el build siguiente (`Successfully installed ... huggingface_hub-0.34.4`).

---

## 2. Imagen demasiado grande — torch + CUDA innecesario

- **Capa:** Build / empaquetado de imagen (BuildKit)
- **Severidad:** 🟠 Alta — fallo intermitente en el paso "Build image".
- **Estado:** ⏳ Pendiente

**Descripción.** Tras resolver las dependencias, Railway reportó *"Failed to build an
image"* en el paso de empaquetado, pese a que `pip install` terminaba OK.

**Causa raíz.** La instalación de `torch==2.6.0` arrastra ~2.7 GB de librerías
NVIDIA CUDA que **no se usan** (la app corre en CPU), generando una imagen de varios
GB que el plan de pago inicial no podía finalizar/almacenar con holgura.

**Evidencia (log de build — descargas CUDA innecesarias):**
```
Downloading torch-2.6.0-...whl (766.7 MB)
Downloading nvidia_cublas_cu12-12.4.5.8-...whl (363.4 MB)
Downloading nvidia_cudnn_cu12-9.1.0.70-...whl (664.8 MB)
Downloading nvidia_cusparse_cu12-12.3.1.170-...whl (207.5 MB)
Downloading nvidia_cufft_cu12-11.2.1.3-...whl (211.5 MB)
Downloading nvidia_nccl_cu12-2.21.5-...whl (188.7 MB)
Downloading triton-3.2.0-...whl (253.2 MB)
```

**Impacto.** Builds lentos, imágenes pesadas, mayor consumo de almacenamiento/RAM y
riesgo de fallo en el empaquetado.

**Solución propuesta (pendiente).** Instalar la build CPU-only de torch:
```
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.6.0+cpu
```
Esto elimina todos los paquetes `nvidia-*` y reduce la imagen en ~2.7 GB.

---

## 3. Conexión a la base de datos falla por IPv6 (Network unreachable)

- **Capa:** Runtime (arranque del contenedor)
- **Severidad:** 🔴 Crítica — la app arrancaba pero se caía al conectar a la BD.
- **Estado:** ✅ Resuelto

**Descripción.** El contenedor iniciaba (`Starting Container`) pero crasheaba en
`main.py:10` (`Base.metadata.create_all(bind=engine)`) al intentar conectar a Supabase.

**Causa raíz.** La cadena de conexión **directa** de Supabase
(`db.<proyecto>.supabase.co:5432`) resuelve a una dirección **IPv6**, y Railway
**no tiene salida IPv6**. Resultado: "Network is unreachable".

**Evidencia (log de runtime):**
```
psycopg2.OperationalError: connection to server at
"db.hkmiztljwvmtrwffaedl.supabase.co" (2600:1f1e:90b:a701:b4d1:af75:385d:9504),
port 5432 failed: Network is unreachable
        Is the server running on that host and accepting TCP/IP connections?
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) ...
```
(Nótese la IP `2600:1f1e:...` → IPv6.)

**Impacto.** El servicio nunca llegaba a `Application startup complete`; healthcheck
en rojo, despliegue inutilizable.

**Solución aplicada.** Cambiar la variable `DATABASE_URL` en Railway por la cadena del
**Connection Pooler (Supavisor)** de Supabase, que sí es alcanzable por IPv4:
```
postgresql://postgres.<ref>:<password>@aws-1-sa-east-1.pooler.supabase.com:6543/postgres
```
(host `...pooler.supabase.com`, usuario `postgres.<ref>`, puerto `6543`).

---

## 4. spaCy no carga en producción (D2 cae en fallback a regex)

- **Capa:** Runtime / build
- **Severidad:** 🟠 Alta — degrada la calidad del análisis de la Dimensión 2.
- **Estado:** ⏳ Pendiente

**Descripción.** La Dimensión 2 (Claridad y Coherencia) debe usar spaCy para
lematización/POS, pero en producción el modelo **no está disponible**.

**Causa raíz.** El `build.sh` **solo predescarga el modelo Whisper**; nunca ejecuta
`python -m spacy download es_core_news_sm`. En `nlp_models.py`, `spacy.load(...)`
falla y el código cae a un **fallback de regex/split** por diseño.

**Evidencia (código):**
- `backend/services/nlp_models.py:17` → `_SPACY_MODEL = "es_core_news_sm"`
- `backend/services/nlp_models.py:35-39` → `spacy.load(...)` con `except` → `Fallback a regex/split`
- `backend/build.sh` → solo descarga Whisper, **no** descarga spaCy.

**Impacto.** D2 no usa NLP real en producción aunque el commit indique
"implementar spaCy + BETO real"; la lematización/POS quedan deshabilitadas.

**Solución propuesta (pendiente).** Añadir al `build.sh` la descarga del modelo
(`python -m spacy download es_core_news_<sm|lg>`) y verificar en logs el mensaje
`[SRV] spaCy cargado OK`.

---

## 5. Modelos de IA degradados respecto al plan

- **Capa:** Calidad del análisis
- **Severidad:** 🟡 Media
- **Estado:** ⏳ Pendiente

**Descripción.** Los modelos en producción son más pequeños que los planificados en
la documentación, por límites de RAM del plan inicial de hosting.

**Causa raíz / Evidencia:**

| Componente | Plan (README) | En producción | Evidencia |
|---|---|---|---|
| Whisper (ASR) | `medium` | `small` | `config.py:12` (default `small`); comentario "small cabe en 512 MB" |
| spaCy | `es_core_news_lg` | `es_core_news_sm` (y en fallback) | `nlp_models.py:17` |

**Impacto.** Mayor WER (la meta es < 10 %) y menor precisión léxica/sintáctica.

**Solución propuesta (pendiente).** Con el plan Hobby ($5, hasta 8 GB RAM) es viable
subir a Whisper `medium` (variable `WHISPER_MODEL_FINAL=medium`) y spaCy
`es_core_news_lg` (cambio en `nlp_models.py` + descarga en `build.sh`). Pico de RAM
estimado ~4–6 GB. Conviene aplicar primero la optimización de imagen (#2).

---

## 6. Secreto `JWT_SECRET` expuesto en el Dockerfile (ARG/ENV)

- **Capa:** Seguridad
- **Severidad:** 🟠 Alta
- **Estado:** ⏳ Pendiente

**Descripción.** BuildKit advierte que se usan datos sensibles como `ARG`/`ENV`,
lo que puede filtrar el secreto en las capas de la imagen.

**Evidencia (log de build):**
```
SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data
(ARG "JWT_SECRET") (line 11)
SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data
(ENV "JWT_SECRET") (line 12)
```

**Impacto.** Riesgo de exposición del secreto de firma JWT en la imagen del contenedor.

**Solución propuesta (pendiente).** Gestionar `JWT_SECRET` como **variable/secreto de
entorno en runtime** (panel de Railway), no horneado en la imagen.

---

## 7. `transformers` se instala dos veces (redundancia de build)

- **Capa:** Eficiencia de build
- **Severidad:** 🟡 Media
- **Estado:** ⏳ Pendiente

**Descripción.** Durante el build se instala `transformers` y luego se **desinstala y
reinstala** otra versión, desperdiciando tiempo.

**Causa raíz.** `requirements.txt` fija `transformers==4.52.4` (instalado por Nixpacks),
y luego `build.sh` instala `requirements-prod.txt` con `transformers==4.46.3`,
forzando un downgrade.

**Evidencia (log de build):**
```
Found existing installation: transformers 4.52.4
Uninstalling transformers-4.52.4 ...
Successfully installed tokenizers-0.20.3 transformers-4.46.3
```

**Impacto.** Builds más lentos y descargas redundantes; inconsistencia de versión
entre archivos de requisitos.

**Solución propuesta (pendiente).** Alinear ambos archivos a una única versión de
`transformers`.

---

## 8. Vercel no desplegó el commit del frontend

- **Capa:** Deploy frontend (Vercel)
- **Severidad:** 🟡 Media
- **Estado:** ✅ Resuelto

**Descripción.** Los cambios de UI (agrupado de métricas técnicas por dimensión en
`Practica.jsx`) estaban en GitHub pero **no se veían** en la app publicada.

**Causa raíz.** El auto-deploy de Vercel no se disparó para el commit `7d30cce`;
la última build de Producción había quedado en el commit anterior `c15eb1a`.

**Evidencia.** En Vercel → Deployments, el deployment de Producción más reciente
correspondía a `c15eb1a`; el commit `7d30cce` (con el cambio del frontend) no figuraba
en la lista de builds.

**Impacto.** La app pública mostraba el diseño antiguo pese a tener el código nuevo
en el repositorio.

**Solución aplicada.** Empujar un commit nuevo (`63d2039`) a ambos remotos para
re-disparar el build de Vercel, que ya incluye los cambios de `7d30cce`.

---

## Anexo — Trazabilidad de commits

| Commit | Descripción | Repos |
|--------|-------------|-------|
| `c15eb1a` | Fix: conflicto de dependencias (`huggingface_hub` → 0.34.4) | origin, upstream |
| `7d30cce` | Frontend: datos técnicos por dimensión + archivos auxiliares | origin, upstream |
| `63d2039` | chore: re-disparar deploy de Vercel | origin, upstream |

**Remotos:**
- `origin` → `github.com/ramdhum-a-s-e/SRV-Oratoria-IA` (fork)
- `upstream` → `github.com/ALS-12321/SRV-Oratoria-IA` (repo del equipo)

**Cadena de progreso del despliegue del backend (Railway):**
`Conflicto pip ❌ → Build OK ✅ → Imagen pesada ⚠️ → Arranque OK ✅ → BD IPv6 ❌ → Pooler IPv4 ✅`
