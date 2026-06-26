# Documentación Técnica — Algoritmos y Métricas del SRV

**Sistema de Retroalimentación por Voz (SRV) basado en IA**
I.E. Juan José Farfán — Lancones, Piura | UPAO 2026

Este documento explica en detalle cómo funciona el código, qué algoritmos usa cada dimensión,
cómo se calcula cada métrica, qué tan confiables son los algoritmos y cómo el sistema se alinea
con el estado del arte de los antecedentes de la investigación.

---

## 1. Visión general y flujo de procesamiento

El SRV recibe el audio del estudiante y lo procesa en una secuencia (pipeline) que produce tres
dimensiones de análisis y un puntaje global. El flujo del endpoint `POST /audio/analizar` es:

1. **Recepción y conversión**: el audio del navegador (WebM/Opus) se convierte a WAV mono 16 kHz
   con PyAV.
2. **Filtros anti-ruido**: filtro paso-alto Butterworth + puerta de ruido (reducen el ruido del
   aula sin dañar la voz).
3. **Transcripción (D1)**: faster-whisper genera el texto y las marcas de tiempo por palabra.
4. **Fluidez (D1)**: velocidad (PPM), pausas/bloqueos y prosodia (Praat).
5. **Vocabulario y coherencia (D2)**: muletillas y riqueza léxica (spaCy) + coherencia (BETO).
6. **Expresividad (D3)**: variación tonal, calidad de voz y volumen (a partir de la prosodia).
7. **Fidelidad de lectura** (solo modo lectura): comparación con el texto original (Levenshtein).
8. **Puntaje global**: combinación ponderada de D1, D2 y D3.
9. **Consejo con IA** (opcional, HU-25): Claude redacta un consejo a partir de los puntajes.
10. **Persistencia y respuesta**: se guardan los resultados; el audio se elimina.

---

## 2. Dimensión 1 — Fluidez oral

Mide la **fluidez mecánica**: velocidad de habla, bloqueos y rasgos prosódicos.

### 2.1 Transcripción (faster-whisper)
Algoritmo: modelo **Whisper** (arquitectura Transformer encoder-decoder) en su implementación
optimizada `faster-whisper` (modelo *medium*, cómputo CPU int8). Se ejecuta con
`word_timestamps=True`, por lo que cada palabra obtiene un inicio y un fin (start, end). El
resultado es una lista de tokens `(palabra, inicio, fin)` y la transcripción completa.

### 2.2 Velocidad de habla (PPM)
Se calcula sobre el **tiempo de habla activa**, excluyendo los bloqueos:

- duración_habla = suma de (fin − inicio) de cada palabra + los silencios cortos entre palabras
  (gap < 1.5 s). Los gaps ≥ 1.5 s se consideran bloqueos y **no** suman tiempo.
- PPM = número de palabras ÷ (duración_habla ÷ 60).

Esto evita que las pausas largas "castiguen" artificialmente la velocidad.

### 2.3 Detección de pausas y bloqueos
Se recorre la secuencia de palabras y se mide el silencio (gap) entre cada par consecutivo:

- gap ≥ 0.5 s → se cuenta como **pausa**.
- gap ≥ 2.0 s → se marca como **pausa larga (bloqueo)**.

Se reportan: total de pausas, total de bloqueos y pausa promedio.

### 2.4 Prosodia (Praat / parselmouth)
Mediante Praat se extraen rasgos acústicos de la señal (también usados por D3):

| Rasgo | Algoritmo de Praat | Significado |
|---|---|---|
| F0 (tono) media y desviación | Autocorrelación (`to_pitch`) | Altura y variación del tono |
| Jitter (local) | PointProcess periódico (cc) | Variación de período (estabilidad de frecuencia) |
| Shimmer (local) | PointProcess periódico (cc) | Variación de amplitud (estabilidad de volumen) |
| HNR | Harmonicidad por correlación cruzada | Relación voz/ruido (claridad) |
| Intensidad | Energía media (RMS → dB) | Volumen |

### 2.5 Puntaje de D1
Se usa un esquema por puntos (0–5) que luego se escala a 0–100:

- **Velocidad**: 3 pts si PPM 80–120 (ideal); 2 pts si 60–80 o 120–140; 1 pt fuera de rango.
- **Bloqueos**: 2 pts si 0 bloqueos; 1 pt si ≤ 1; 0 pts si más.
- score_D1 = (pts_velocidad + pts_bloqueos) ÷ 5 × 100. Estrellas = pts (acotado 1–5).

### 2.6 Confiabilidad de D1
- La **transcripción** con Whisper *medium* en español es de alta calidad, pero su precisión
  disminuye con voz infantil y ruido de aula; por eso se aplican los filtros previos. La meta de
  WER < 10% debe validarse empíricamente con datos reales.
- El **PPM** y la **detección de pausas** son deterministas y confiables **siempre que** las
  marcas de tiempo de Whisper sean correctas; dependen de la calidad de la transcripción.
- Los **rasgos de Praat** son medidas estándar y científicamente validadas en fonética, por lo que
  su extracción es altamente confiable.

---

## 3. Dimensión 2 — Vocabulario y coherencia

Mide **qué** y **cómo** dice el estudiante: muletillas, variedad de vocabulario y coherencia.

### 3.1 Muletillas (spaCy + regex)
Dos mecanismos combinados:
- **Regex** para sonidos de relleno alargados que no son palabras reales (eh, ah, em, um, mm,
  "esteee").
- **spaCy** (modelo `es_core_news_lg`): se lematiza el texto y se detectan lemas de relleno
  ("este", "pues", "bueno", "osea", "entonces", "digamos", "tipo", etc.).
- tasa de muletillas = (total de muletillas ÷ total de palabras) × 100.
- Si spaCy no carga, hay un **fallback** por coincidencia de palabras.

### 3.2 Riqueza léxica (TTR)
- Con spaCy se extraen los **lemas de contenido** (alfabéticos, sin stopwords, longitud ≥ 2).
- TTR (Type-Token Ratio) = palabras únicas ÷ palabras totales. Mide qué tan variado es el
  vocabulario (1 = no repite nada; valores bajos = vocabulario repetitivo).

### 3.3 Coherencia semántica (BETO)
- El texto se divide en oraciones (segmentos de más de 8 caracteres).
- Con **BETO** (BERT en español, `bert-base-spanish-wwm-cased`) se obtiene un *embedding* (vector
  de significado) por oración.
- Se calcula la **similitud coseno** entre oraciones consecutivas y se promedia. Una similitud
  alta indica que las ideas están conectadas (discurso coherente).
- Si BETO no está disponible, se usa **Jaccard** (solapamiento de palabras) como respaldo. Si el
  texto es muy corto (< 2 oraciones), se asigna un valor neutral alto para no penalizar.

### 3.4 Puntaje de D2 (0–100)
| Componente | Puntos | Reglas |
|---|---|---|
| Muletillas | 0–40 | ≤1 → 40; ≤4 → 25; ≤8 → 10; 9+ → 0 |
| TTR | 0–35 | > 0.50 → 35; > 0.30 → 20; ≤ 0.30 → 5 |
| Coherencia | 0–25 | Umbrales según método: BETO (0.86 / 0.79) o Jaccard (0.35 / 0.15) |

> Nota: los umbrales de coherencia se calibran por método porque BETO da cosenos comprimidos en
> rango alto (~0.75–0.95), mientras que Jaccard da valores bajos (~0–0.4).

### 3.5 Confiabilidad de D2
- **TTR y muletillas** (spaCy): conteos léxicos confiables; la principal limitación es que las
  muletillas solo se detectan si el ASR las transcribió.
- **Coherencia** (BETO): es el estado del arte para similitud semántica en español; aporta una
  medida de coherencia mucho más fiel que el conteo de palabras. Es un **proxy** de coherencia
  (no un juicio absoluto), y sus umbrales son calibrados, no validados contra jueces humanos.

---

## 4. Dimensión 3 — Expresividad vocal

Mide la **expresividad** de la voz mediante un *proxy acústico* (no reconoce emociones). Reutiliza
los rasgos de Praat extraídos en D1.

### 4.1 Componentes y fórmulas (0–100)
| Componente | Puntos | Fórmula |
|---|---|---|
| Variación tonal | 0–40 | CV = f0_std ÷ f0_mean; pts = mín(40, CV × 114.3) |
| Calidad de voz (HNR) | 0–30 | pts = mín(30, HNR ÷ 25 × 30) |
| Volumen (intensidad) | 0–30 | 55–75 dB → 30; 45–55 ó 75–85 → 15; resto → 5 |

- **Variación tonal**: el coeficiente de variación de F0 distingue una voz **expresiva** (entona,
  CV alto) de una **monótona** (CV bajo). Es el indicador principal de expresividad.
- **Calidad (HNR)**: HNR > 20 dB indica voz limpia; valores bajos indican ronquera/ruido.
- **Volumen**: premia el rango de proyección típico de un niño en aula.
- score_D3 = variación + calidad + volumen.

### 4.2 Confiabilidad de D3
- Los **rasgos acústicos** provienen de algoritmos de Praat estándar y validados (autocorrelación
  para tono y armonicidad, energía para volumen), por lo que su medición es confiable.
- El **mapeo a "expresividad"** mediante el CV de F0 es un proxy razonable y usado en la
  literatura, pero es una **heurística**: aproxima la expresividad, no la mide de forma absoluta.
  El modelo emocional (Wav2Vec2) quedó fuera de alcance.

---

## 5. Modo lectura — Fidelidad (Levenshtein / WER)

En modo lectura se compara lo que el alumno **leyó** (transcripción) con el **texto original**:

- Ambos textos se normalizan (minúsculas, sin tildes ni puntuación) y se separan en palabras.
- Se calcula la **distancia de Levenshtein a nivel de palabra** (programación dinámica:
  inserciones, eliminaciones y sustituciones).
- WER (Word Error Rate) = distancia ÷ número de palabras del texto original.
- fidelidad = (1 − WER) × 100.

**Confiabilidad**: el WER es una métrica **exacta, determinista y estándar** en reconocimiento del
habla. Importante: en modo lectura el WER combina errores del ASR con errores reales de lectura
del niño; para medir el WER del reconocedor "puro" se requiere una transcripción humana de
referencia.

---

## 6. Puntaje global

Combina las tres dimensiones con una ponderación fija:

- score_global = 0.40 × D1 + 0.35 × D2 + 0.25 × D3 (rango 0–100).
- Se asignan nivel, color y estrellas según el puntaje (p. ej. ≥ 85 Sobresaliente / 5★;
  ≥ 70 Bueno / 4★; ≥ 50 En desarrollo / 3★; etc.).

La fluidez (D1) tiene el mayor peso por ser el objetivo central del proyecto, seguida del
vocabulario/coherencia (D2) y la expresividad (D3).

---

## 7. Retroalimentación con IA generativa (HU-25, opcional)

De forma opcional y desactivable, el sistema envía **solo los puntajes numéricos** (D1, D2, D3,
PPM, bloqueos, muletillas) a **Claude Haiku**, que redacta un consejo motivador en español simple
para el niño. Nunca se envía la voz ni la transcripción. Si está desactivado o falla, se usan los
consejos por reglas (fallback).

---

## 8. ¿Qué tan confiables son los algoritmos? (síntesis)

| Etapa | Confiabilidad | Observación |
|---|---|---|
| Transcripción (Whisper medium) | Alta (con matices) | Baja con ruido/voz infantil; mitigada con filtros; validar WER |
| PPM y pausas | Alta | Deterministas; dependen de los timestamps del ASR |
| Prosodia (Praat) | Muy alta | Algoritmos estándar y validados en fonética |
| Muletillas y TTR (spaCy) | Alta | Limitadas por lo que el ASR transcriba |
| Coherencia (BETO) | Media-alta | Estado del arte en semántica; umbrales calibrados (proxy) |
| Fidelidad de lectura (WER) | Muy alta | Métrica exacta y estándar |
| Puntaje (reglas/umbrales) | Transparente y reproducible | Heurístico; conviene validarlo contra evaluadores humanos (trabajo futuro) |

**Conclusión de confiabilidad:** la **extracción de características** se apoya en herramientas del
estado del arte (Whisper, Praat, spaCy, BETO), altamente confiables. La **conversión a puntajes**
es por reglas: es transparente, reproducible y explicable, pero sus umbrales son heurísticos; su
validación frente a calificaciones de expertos y la medición empírica del WER quedan como trabajo
futuro. Esta decisión (reglas en lugar de un modelo entrenado) es adecuada ante la ausencia de un
conjunto de datos etiquetado de voz infantil.

---

## 9. Alineación con el estado del arte (antecedentes)

A continuación se contrasta el SRV con los seis antecedentes de la investigación.

| Antecedente | Enfoque | Relación con el SRV |
|---|---|---|
| Cevallos & Gómez (2021) | ASR (DNN+HMM) para lectura en escolares (español) | Mismo dominio (niños, lectura, español); el SRV usa un ASR más moderno (Whisper) |
| Sánchez et al. (2024) | SRS como apoyo a la pronunciación (EFL) | Comparte el rol de herramienta de feedback complementaria y autonomía |
| García Pazos et al. (2025) | Revisión sistemática de software SRS | Encuadra el estado del arte de herramientas de reconocimiento |
| Jinga et al. (2024) | VR adaptativo para hablar en público; feedback en vivo + resumen | Mismo modelo de feedback (en vivo + resumen); el SRV es web, no VR |
| Haider et al. (2020) | Scoring automático de presentación oral + feedback | Comparador directo: mismo objetivo (puntuar oratoria y generar feedback) |
| Sonnleitner et al. (2025) | Modelos simples (LASSO) superan a ML complejo con pocos datos | Sustenta el uso de un esquema por reglas ante datos escasos |

### 9.1 Posicionamiento por eje
| Eje | Estado del arte | SRV | Nivel |
|---|---|---|---|
| ASR | DNN+HMM, audiovisual+SOM, SRS | Whisper (Transformer) con timestamps | A la par / por delante |
| Semántica | Poco abordada | BETO (BERT en español) | A la par (estado del arte) |
| Prosodia | Rasgos acústicos (p. ej. OpenSMILE) | Praat: F0, jitter, shimmer, HNR | Equivalente |
| Scoring | Clasificación ML / LASSO | Reglas (umbrales) | Por debajo, justificado por falta de datos |
| Despliegue | VR inmersiva / video | Web accesible | Distinto (viabilidad rural) |
| Población | Adultos / EFL / superior | Niños 1.° grado rural, español | Aporte diferencial |

### 9.2 Conclusión sobre el estado del arte
El SRV **se sitúa dentro del umbral del estado del arte en su núcleo tecnológico** (Whisper, BETO
y Praat), e incluso adelanta en ASR a los antecedentes más antiguos. Su diferencia respecto al
estado del arte está en el **scoring por reglas** (en lugar de un clasificador entrenado), decisión
justificada por la ausencia de un dataset etiquetado de voz infantil y respaldada por Sonnleitner
et al. (2025). El **aporte** del proyecto no es superar un algoritmo, sino **trasladar el estado del
arte a un contexto no atendido** (niños de primer grado, zona rural, idioma español) de forma
ética (procesamiento local, audio efímero) y desplegable a bajo costo.

---

## 10. Referencias

- Cevallos Correa, F. L., & Gómez Ríos, M. D. (2021). Reconocimiento automático de voz aplicado a la mejora en el proceso de aprendizaje de lectura en nivel escolar. Universidad Politécnica Salesiana, Ecuador.
- García Pazos, E. A., et al. (2025). Software de reconocimiento de voz para el desarrollo de la pronunciación de inglés: Una revisión sistemática. RITI Journal, 13(29).
- Haider, F., et al. (2020). An Active Data Representation of Videos for Automatic Scoring of Oral Presentation Delivery Skills and Feedback Generation. Frontiers in Computer Science, 2, 1.
- Jinga, N., et al. (2024). Overcoming Fear and Improving Public Speaking Skills through Adaptive VR Training. Electronics, 13(11), 2042.
- Sánchez, L., et al. (2024). Speech Recognition Software as a Tool to Enhance EFL Learners' Pronunciation. Lengua y Sociedad, 23(2).
- Sonnleitner, B., et al. (2025). Evaluation of early student performance prediction given concept drift. Computers and Education: Artificial Intelligence, 8, 100369.

*Documento de uso académico — Taller de Tesis, UPAO 2026.*
