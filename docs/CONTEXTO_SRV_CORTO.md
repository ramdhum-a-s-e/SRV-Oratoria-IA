# SRV-Oratoria-IA — contexto breve (pegar como system prompt)

**Proyecto:** Sistema de Retroalimentación por Voz (SRV) basado en IA para evaluar la **fluidez de
oratoria en educación primaria** (español). UPAO 2026. Autores: Lezcano Saavedra Anthony y Arévalo
Espinoza Ramdhum. Docente: Mg. Walter Manuel Cueva Chávez. Contexto real: I.E. Juan José Farfán,
Lancones (Piura), rural. Repo: github.com/ALS-12321/SRV-Oratoria-IA.

**Regla de oro:** no inventar datos. Lo no medido se marca "pendiente / no aplica".

**Qué es:** app web que graba la voz del alumno, la procesa con IA y devuelve retroalimentación en
3 dimensiones + puntaje global + estrellas + consejos + reporte PDF + historial + panel docente (RBAC).
Aporte: trasladar el estado del arte (Whisper + BETO/spaCy + Praat) a un nicho no atendido, de forma
ética (audio local y **efímero**) y de bajo costo. No es un algoritmo nuevo.

**Stack:** React 19 + Vite (Vercel) · FastAPI + Python 3.11 (Railway) · PostgreSQL/Supabase (SQLite dev) ·
faster-whisper medium int8 (ASR) · praat-parselmouth (prosodia) · spaCy es_core_news_lg + BETO (NLP) ·
PyAV (WAV 16 kHz) · JWT HS256 + Argon2 · ReportLab (PDF) · Claude Haiku opcional (solo métricas).

**Pipeline** `POST /audio/analizar`: audio→WAV 16 kHz + filtros anti-ruido→transcripción determinista
(beam_size=1, temperature=0.0)→**guard: válido solo si ≥10 palabras y ≥5 s**→D1/D2/D3→scoring→se **borra el audio**.

**Dimensiones y puntaje (reglas, no ML):**
- **score_global = 0.40·D1 + 0.35·D2 + 0.25·D3** (0–100). Estrellas: ≥85=5★, ≥70=4★, ≥50=3★, ≥30=2★, <30=1★.
- D1 Fluidez: PPM (ideal 80–120; bloqueo=pausa ≥2 s) + prosodia Praat (F0, jitter, shimmer, HNR).
- D2 Vocab/coherencia: muletillas (spaCy+regex) + TTR + coherencia coseno con BETO.
- D3 Expresividad: CV de F0 + HNR + volumen.
- Modo lectura: **WER = Levenshtein(palabras)/N_ref**; fidelidad=(1−WER)·100.
- Pesos 40/35/25 y varios umbrales son **heurísticos** (no validados con jueces humanos).

**Validaciones (DTO), útiles para caja negra:** nombre/apellido 2–50 solo letras; usuario 3–30 solo
letras y único; contraseña 6–128 alfanumérica (Argon2); rol alumno|docente. Login malo→401.
RBAC: alumno→panel docente=403; sin token/expirado=401.

**Metodología:** Scrum, 2 sprints. Backlog 50 ítems (28 HU + 22 TA, 189 pts). **48/50 hechos**;
pendiente HU-27 (banco de textos por docente); TA-012 "no aplica" (sin Alembic). 68 commits.

**Pruebas:** suite pytest (auth, rbac, determinismo, scoring/guards, feedback, metrics, audio) OK.
25 casos manuales en 5 módulos (xlsx). **Determinismo end-to-end (Colab, real):** 2 audios × 10 corridas,
13 métricas con **desviación estándar = 0** (P1: PPM 116.1/global 88.7; P2: PPM 60.2/global 56.2).
→ Valida **reproducibilidad**, NO exactitud.

**PENDIENTE / NO APLICA (no inventar):** WER<10% sin medir con voz infantil real; comparación con línea
base numérica; test estadístico (p-value/IC); usabilidad SUS; partición train/test = no aplica (no se
entrena, usa preentrenados + reglas); dataset propio = no hay (audio efímero); **Anexo A: el diagrama de
arquitectura NO existe como figura, hay que crearlo**.

**Docs clave (carpeta docs/):** ARQUITECTURA.docx, DOCUMENTACION_TECNICA_ALGORITMOS.docx,
CRITERIOS_EVALUACION.docx, COMPARATIVA_ANTECEDENTES.docx (6 antecedentes), PRODUCT_BACKLOG_ACTUALIZADO.docx,
"Casos de Prueba SRV-Oratoria-IA.xlsx". Generados: INFORME TECNICO SRV_LLENO.docx (TDDR con determinismo),
PLAN DE PRUEBAS CAJA NEGRA SRV.docx, y **CONTEXTO_SRV_PARA_IA.md** (contexto completo).
