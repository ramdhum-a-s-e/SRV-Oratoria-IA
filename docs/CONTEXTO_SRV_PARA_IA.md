# Contexto del proyecto SRV-Oratoria-IA (handoff para otras conversaciones)

> Documento de traspaso generado el 2026-07-13. Reúne los datos **reales y verificados**
> del proyecto (código, documentos y pruebas) más el resumen de la conversación en la que
> se generó. Pensado para pegarse/adjuntarse en otra IA o sesión y continuar el trabajo sin
> perder contexto. **Regla de oro del proyecto: no inventar datos; lo no medible se marca como
> "pendiente / no aplica".**

---

## 1. Identidad del proyecto

- **Título:** Sistema de Retroalimentación por Voz (SRV) basado en Inteligencia Artificial para la
  evaluación de la fluidez de oratoria en educación primaria.
- **Universidad:** Universidad Privada Antenor Orrego (UPAO) — Facultad de Ingeniería —
  Programa de Estudio de Ingeniería de Sistemas e Inteligencia Artificial.
- **Autores:** Br. Lezcano Saavedra, Anthony; Br. Arévalo Espinoza, Ramdhum.
- **Docente:** Mg. Walter Manuel Cueva Chávez.
- **Contexto de despliegue (caso real):** I.E. Juan José Farfán — Lancones, Piura (escuela rural, español).
  El documento académico se firma en Trujillo – Perú, 2026.
- **Repositorio:** https://github.com/ALS-12321/SRV-Oratoria-IA  (68 commits al 2026-07-13).
- **Scrum Master:** Ramdhum Arévalo Espinoza.
- **Aporte central:** no es un algoritmo nuevo, sino **trasladar el estado del arte
  (Whisper + BETO/spaCy + Praat) a un dominio poco atendido** (oratoria infantil en español, rural),
  de forma **ética (privacy by design: audio local y efímero)** y **de bajo costo**.

---

## 2. Qué hace el sistema

Aplicación web cliente-servidor: captura la voz del estudiante, la procesa con IA y devuelve
retroalimentación formativa en **3 dimensiones** + puntaje global + estrellas + consejos + reporte PDF +
historial/gráficos + panel docente con control de acceso por roles.

**Dimensiones:**
- **D1 – Fluidez oral** (peso 0.40): velocidad (PPM), pausas/bloqueos, prosodia (Praat).
- **D2 – Vocabulario y coherencia** (peso 0.35): muletillas + TTR (spaCy), coherencia semántica (BETO).
- **D3 – Expresividad vocal** (peso 0.25): variación tonal (CV de F0), calidad (HNR), volumen (intensidad).

---

## 3. Arquitectura y stack (real, con versiones)

Arquitectura de **3 niveles**:
- **Cliente (navegador):** SPA React + Vite en Vercel; captura audio con WaveSurfer (onda en tiempo real),
  sesión con JWT, consume API por HTTPS.
- **API (servidor):** FastAPI (Uvicorn) en Railway; expone endpoints, ejecuta el pipeline de IA, persiste.
- **Base de datos:** PostgreSQL en Supabase (SQLite en desarrollo), vía SQLAlchemy (pooler IPv4).
- **Servicio externo opcional:** Anthropic Claude Haiku (HU-25) para consejos; solo se le envían métricas numéricas.

| Capa | Tecnología | Versión / detalle |
|---|---|---|
| Frontend | React + Vite | React 19 / Vite 8; React Router, WaveSurfer.js, Chart.js, Axios |
| Backend | FastAPI (Uvicorn) | FastAPI 0.136 / Python 3.11 |
| Base de datos | PostgreSQL (Supabase) / SQLite dev | SQLAlchemy 2.0 |
| ASR | faster-whisper | 1.2.1, modelo **medium**, CPU **int8**; + CTranslate2 4.7.1 |
| Prosodia | praat-parselmouth | 0.4.5 |
| NLP | spaCy (es_core_news_lg) + BETO | spaCy 3.8 / transformers 4.52 / torch 2.6+cpu; BETO = dccuchile/bert-base-spanish-wwm-cased |
| Audio | PyAV (av) | 17.0.1; convierte a WAV mono 16 kHz + filtros anti-ruido |
| Auth | python-jose + passlib[argon2] | JWT HS256 / Argon2 |
| Reportes | ReportLab | 4.2.5 (PDF) |
| IA generativa (opcional) | Anthropic Claude Haiku | anthropic 0.111 (desactivada por defecto) |
| Despliegue | Railway / Vercel / Supabase | Nixpacks; build.sh predescarga modelos; HTTPS gestionado |

**Reformulación respecto al Charter S04:** de AWS/NestJS/Angular → FastAPI/React con Railway/Supabase/Vercel
(por costo, privacidad y simplicidad). Migraciones sin Alembic (micro-migración `ensure_schema()`).

---

## 4. Pipeline de procesamiento (endpoint `POST /audio/analizar`)

1. Cliente envía audio grabado (WebM/Opus) por HTTPS con token JWT.
2. Conversión a WAV mono 16 kHz (PyAV) + **filtros anti-ruido** (paso-alto Butterworth + puerta de ruido).
3. Transcripción con **faster-whisper** (timestamps por palabra), decodificación **fija/determinista**:
   `beam_size=1, temperature=0.0, condition_on_previous_text=False, vad_filter=True`.
4. **Guard de contenido mínimo** (services/validation.py): la sesión es válida solo si
   **≥ 10 palabras Y ≥ 5 s de habla efectiva**; si no, `sesion_valida=false`, no puntúa ni guarda.
5. D1 (PPM, pausas, prosodia), D2 (muletillas/TTR/coherencia), D3 (expresividad), modo lectura (WER).
6. Puntaje global + estrellas.
7. (Opcional) consejo con Claude a partir de solo números.
8. Persiste sesión y resultados; **elimina el audio** (efímero; persistencia desactivada por defecto).

---

## 5. Algoritmos y fórmulas (reales, del código)

### Puntaje global (services/scoring.py)
```
score_global = 0.40*D1 + 0.35*D2 + 0.25*D3     # 0-100
```
Cortes de nivel/estrellas: ≥85 Sobresaliente/5★ · ≥70 Bueno/4★ · ≥50 En desarrollo/3★ ·
≥30 Necesita apoyo/2★ · <30 Inicio/1★.

### D1 – Fluidez
- **PPM** = nº palabras / (duración_habla_activa/60). Se excluyen del tiempo los gaps ≥ 1.5 s (bloqueos).
- **Pausas:** gap ≥ 0.5 s = pausa; gap ≥ 2.0 s = pausa larga / bloqueo.
- **Prosodia (Praat):** F0 media/desv, jitter, shimmer, HNR, intensidad. Rango pitch calibrado a voz
  infantil (PITCH_FLOOR 100 Hz / CEILING 500 Hz).
- **Scoring D1 continuo (rampas lineales, no escalones):** velocidad 60% (meseta 100 en 80–120 PPM,
  baja a 0 en 40 y 160) + pausas 40% (0 bloqueos=100; −25 por bloqueo).

### D2 – Vocabulario/coherencia (0–100 = muletillas 0–40 + TTR 0–35 + coherencia 0–25)
- **Muletillas:** regex (eh, ah, em, um, mm, "esteee") + lemas spaCy (este, pues, bueno, osea, entonces…).
  40 pts con 0–1; −5 por cada extra.
- **TTR** = tipos/tokens (sobre lemas de contenido). Rampa: 0.30→20 pts, 0.50→35 pts.
- **Coherencia:** similitud coseno media entre oraciones con **BETO**; umbrales por método
  (BETO 0.86/0.79; Jaccard 0.35/0.15). Texto < 2 oraciones → valor neutral (no penaliza).

### D3 – Expresividad (0–100 = variación 0–40 + HNR 0–30 + volumen 0–30)
- **Variación tonal:** CV de F0 = f0_std/f0_mean; pts = min(40, CV·114.3).
- **Calidad:** pts = min(30, HNR/25·30).
- **Volumen:** meseta 30 en 55–75 dB; rampa a 0 en 35 y 95 dB.

### Modo lectura – Fidelidad / WER (services/dimension1/reading.py)
```
WER = distancia_Levenshtein(palabras_ref, palabras_hyp) / nº_palabras_ref
fidelidad = (1 - WER) * 100
```
Umbrales: ≥90 excelente · ≥70 bueno · ≥50 regular · <50 bajo.

> **Respaldo académico de los criterios** (de CRITERIOS_EVALUACION.docx): PPM=Hasbrouck & Tindal (2017);
> pausas=Bortfeld et al. (2001); TTR=Templin (1957), MTLD/VOCD=McCarthy & Jarvis (2010);
> coherencia=Foltz, Kintsch & Landauer (1998), BETO=Cañete et al. (2020). **Los pesos 40/35/25 y varios
> umbrales son heurísticos (decisión de diseño), no validados contra jueces humanos.**

---

## 6. Validaciones reales (DTO – schemas/auth.py) — clave para pruebas de caja negra

- **nombre / apellido:** 2–50 caracteres, **solo letras** (incl. tildes/ñ), sin números/espacios/símbolos.
- **username:** 3–30, **solo letras** (A–Z); además **único** (400 "El nombre de usuario ya existe").
- **password:** 6–128, **solo letras y números** (sin especiales/espacios); se guarda con **Argon2**.
- **rol:** alumno | docente (si no → "Rol invalido").
- **grado:** opcional, ≤10, letras/números/°º. **seccion:** opcional, 1–2 letras.
- Login inválido → 401 "Usuario o contraseña incorrectos".
- **RBAC:** `require_docente` → 403 "Solo para docentes"; sin token/expirado → 401.

---

## 7. Endpoints (routers/)

- `POST /auth/register` (201 + JWT) · `POST /auth/login` (JWT) · `GET /auth/me`
- `GET /audio/textos` · `POST /audio/analizar` (pipeline completo; form: file, modo, texto_id)
- `GET /metrics/historial` · `GET /metrics/docente/alumnos` · `GET /metrics/docente/alumno/{id}` ·
  `GET /metrics/sesion/{id}` · `GET /metrics/reporte/{id}` (PDF)

## 8. Modelo de datos

- `usuarios` (rol alumno/docente, password_hash Argon2, grado, seccion)
- `textos_lectura` (cuentos 1.º grado sembrados al inicio)
- `sesiones` (usuario, modo lectura/libre, texto_id) — **1 usuario → N sesiones**
- `resultados_d1` / `resultados_d2` / `resultados_d3` — **1 sesión → 1 resultado por dimensión**
  (D1 guarda transcripción, ppm, pausas, prosodia, score, feedback_json, audio_path nullable)

---

## 9. Metodología y backlog (PRODUCT_BACKLOG_ACTUALIZADO.docx)

- **Scrum, 2 sprints.** Backlog: **50 ítems = 28 HU + 22 TA**, **189 story points**.
- Sprint 1 (hasta 07/06/2026): 26/26 (100%). Sprint 2 (hasta 05/07/2026): 21/24 (~92%).
- **48/50 completados.** Pendiente: **HU-27** (banco de textos por docente). **TA-012** = "no aplica"
  (migración resuelta sin Alembic).
- Ramas: `main`, `feature/logica-negocio-srv`, `mejora-determinismo-scoring` (feature branches + PR).

---

## 10. Pruebas

### Suite automatizada (backend/tests, pytest)
test_auth, test_rbac, test_determinismo, test_scoring_guards, test_feedback, test_metrics,
test_audio, test_ia, test_unit. (Se ejecutan sin fallos.)

### Casos de prueba manuales ("Casos de Prueba SRV-Oratoria-IA.xlsx")
**25 casos en 5 módulos:** Seguridad/Acceso (1.1–1.5), Audio/ASR (2.1–2.5), D1-Fluidez (3.1–3.5),
D2/D3-NLP y Voz (4.1–4.5), Resultados/Reportes (5.1–5.5).

### ✅ Pruebas de determinismo end-to-end (2 notebooks Colab, REALES)
Se subió un audio y se ejecutó `/audio/analizar` **10 veces**; se compararon 13 métricas.
- **Prueba 1** (audio 101 palabras, modo libre): transcripción idéntica, **13 métricas con std = 0**.
  PPM 116.1 · **global 88.7** (D1=100, D2=80, D3=82.6) · TTR 0.984 · F0 127.4 Hz · jitter 2.56% · HNR 10.52 dB.
- **Prueba 2** (audio 50 palabras, modo libre): idéntico, **13 métricas con std = 0**.
  PPM 60.2 · **global 56.2** (D1=30.3, D2=72.5, D3=74.7) · TTR 0.889 · F0 155.1 Hz · jitter 6.29% · HNR 3.92 dB.
- **Conclusión:** pipeline **100% determinista** (mismo audio → mismo resultado), por la decodificación fija
  de Whisper + scoring por reglas. **Valida reproducibilidad, NO exactitud/WER.**
- Links: notebook 1 `1R7yiwZk_xOC6R6Aw3ND1ofFtlWMFYyg3`, notebook 2 `1wXq4s4twWNwCtIsCOK4Yu3UTvm16VmIi`
  (Google Colab/Drive; solo accesibles vía descarga directa del .ipynb).

### Base de datos de desarrollo (backend/srv_dev.db)
Solo **1 sesión de prueba** del desarrollador (modo libre, N=1, sin WER). No es dataset de validación.

---

## 11. Estado de validación: qué está probado y qué NO (honesto)

**Probado / verificado:** funcionamiento del pipeline, validaciones DTO, RBAC, scoring por reglas,
suite pytest, **determinismo/reproducibilidad** (numérico, std=0).

**Pendiente / no aplica (NO inventar cifras):**
- **WER < 10% (meta OD2):** el sistema calcula WER por sesión, pero **no hay medición formal** con voz
  infantil real en modo lectura. Las pruebas de determinismo fueron en modo libre (sin WER).
- **Comparación con línea base (numérica):** pendiente (no hay baseline medido en iguales condiciones).
- **Análisis estadístico (p-value, IC, t-test/Wilcoxon):** pendiente (falta muestra).
- **Estudio de usabilidad (SUS):** no realizado.
- **Partición train/test:** **no aplica** (no se entrenan modelos; se usan preentrenados + reglas).
- **Anexo A "diagrama de arquitectura en alta resolución":** **NO existe** como figura; ARQUITECTURA.docx
  describe la arquitectura en texto/tablas sin imagen. Hay que crearlo (draw.io/Lucidchart) y exportarlo.
- **Dataset propio:** no existe (audio efímero); se usan modelos preentrenados de terceros.

---

## 12. Estado del arte / antecedentes (COMPARATIVA_ANTECEDENTES.docx)

6 antecedentes directos:
1. Cevallos & Gómez (2021) — ASR (DNN+HMM) para lectura escolar, niños español, estudio teórico.
2. Sánchez et al. (2024) — SRS para pronunciación EFL, 10 universitarios, cualitativo.
3. García Pazos et al. (2025) — revisión sistemática SRS (inglés).
4. Jinga et al. (2024) — RV para hablar en público, adultos.
5. Haider et al. (2020) — scoring automático de presentación (descriptores AV + SOM), adultos.
6. Sonnleitner et al. (2025) — ML/LASSO, concept drift, educación superior (respalda "lo simple > ML con pocos datos").

**Posicionamiento:** en ASR el SRV iguala/supera a [1] y [5]; en scoring queda por debajo de enfoques ML
[5][6] pero justificado por falta de dataset etiquetado. Aporte diferencial: población (niños 1.º grado,
rural, español) + ética (audio local/efímero).

---

## 13. Referencias base (18; completar a ≥20, ≥70% recientes, ≥60% Q1/Q2, IEEE/APA 7)

[1] Cevallos & Gómez (2021). [2] Sánchez et al. (2024), Lengua y Sociedad. [3] García Pazos et al. (2025),
RITI. [4] Jinga et al. (2024), Electronics. [5] Haider et al. (2020), Frontiers in Computer Science.
[6] Sonnleitner et al. (2025), Computers and Education: AI. [7] Radford et al. (2023) Whisper, ICML.
[8] Cañete et al. (2020) BETO. [9] Devlin et al. (2019) BERT. [10] Vaswani et al. (2017) Attention Is All You Need.
[11] Boersma & Weenink (2021) Praat. [12] Honnibal & Montani (2017) spaCy. [13] Levenshtein (1966).
[14] Hasbrouck & Tindal (2017) ORF Norms. [15] Bortfeld et al. (2001) Disfluency rates.
[16] Templin (1957). [17] McCarthy & Jarvis (2010) MTLD/vocd-D/HD-D. [18] Foltz, Kintsch & Landauer (1998).

---

## 14. Documentos del proyecto (carpeta docs/)

**Fuentes primarias:** ARQUITECTURA.docx, DOCUMENTACION_TECNICA_ALGORITMOS.docx, CRITERIOS_EVALUACION.docx,
COMPARATIVA_ANTECEDENTES.docx, PRODUCT_BACKLOG_ACTUALIZADO.docx, INFORME_SOLUCION_TECNOLOGICA_SRV.docx,
INFORME_CAPSTONE_SRV.docx, JUSTIFICACIONES_CHARTER.docx, MANUAL_USUARIO.docx, "Casos de Prueba SRV-Oratoria-IA.xlsx".

**Generados en la conversación de traspaso:**
- `INFORME TECNICO SRV.docx` — plantilla TDDR llenada (versión previa a los datos de determinismo).
- `INFORME TECNICO SRV_LLENO.docx` — TDDR lleno **incluyendo** los resultados de determinismo (5.1, 5.4, 6.2, 7).
- `INFORME TECNICO SRV_ORIGINAL_PLANTILLA.docx` — respaldo de la plantilla vacía.
- `PLAN DE PRUEBAS CAJA NEGRA SRV.docx` — plan de pruebas de caja negra (7 escenarios; formato "inHealth"),
  con marcadores para adjuntar capturas y registrar errores observados.
- `INFORME_TECNICO_TDDR_SRV.docx` — versión previa del TDDR (existía antes; el usuario pidió no usarla como fuente).

---

## 15. Resumen de la conversación de traspaso (decisiones tomadas)

1. **Llenar `INFORME TECNICO SRV.docx` (plantilla TDDR).** Decisión del usuario: **llenar desde cero**
   leyendo código y docs (sin usar el TDDR previo). Se preservó estructura/encabezados/tablas y se
   reemplazó el texto-guía por contenido real; lo no medible quedó como "pendiente/no aplica".
2. Se aclaró la diferencia entre "el sistema calcula métricas" y "no hay campaña de medición" (por eso 5.4–5.6
   quedaron pendientes al inicio).
3. El usuario aportó **2 pruebas de determinismo (Colab)** → se leyeron completas (vía descarga del .ipynb),
   son **mediciones reales** que validan **reproducibilidad**; se incorporaron a `INFORME TECNICO SRV_LLENO.docx`.
   (El link normal de Colab no es fetcheable; sí la descarga directa del .ipynb de Drive, o un .py.)
4. Se generó el **Plan de Pruebas de Caja Negra** siguiendo el formato de un PDF de referencia (inHealth),
   con escenarios grounded en las validaciones reales del código y los 25 casos del Excel.
5. **Pendiente del usuario:** capturas de pantalla de la app corriendo, registrar errores observados,
   crear el diagrama de arquitectura (Anexo A), y —si se desea validar WER/estadística/usabilidad— recolectar
   datos reales con estudiantes.

---

## 16. Cómo trabajar con los .docx (utilidad técnica)

- Extraer texto/tablas de un .docx: `python-docx` (`import docx; docx.Document(path)`).
- Excel .xlsx del proyecto usa **inlineStr** (no sharedStrings); leer `xl/worksheets/sheetN.xml` directo.
- Entorno: Windows, Python 3.13 global (usar `PYTHONIOENCODING=utf-8` para imprimir tildes/emoji).
- **Persistencia de audio y frontend:** la persistencia del audio se maneja solo en backend/BD; el frontend
  no cambia por eso.
