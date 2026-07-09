# Criterios de evaluación del SRV — Sistema de Retroalimentación por Voz

> Anexo técnico. Documenta **cómo** el sistema califica cada dimensión, los
> umbrales exactos implementados en el código y el **sustento** de cada criterio.
> La columna *Respaldo* distingue lo que tiene base académica de lo que es una
> **calibración heurística** (decisión de diseño que conviene justificar o
> validar empíricamente con audios reales de niños).

## 1. Estructura general del puntaje

El puntaje global (0–100) es una combinación ponderada de tres dimensiones:

| Dimensión | Qué mide | Peso | Archivo |
|-----------|----------|------|---------|
| D1 — Fluidez oral | Velocidad y bloqueos al hablar | **40 %** | `services/dimension1/` |
| D2 — Léxico y coherencia | Muletillas, riqueza y conexión de ideas | **35 %** | `services/dimension2/` |
| D3 — Expresividad vocal | Tono, calidad de voz y volumen | **25 %** | `services/dimension3/` |

`score_global = 0.40·D1 + 0.35·D2 + 0.25·D3`  · *(`services/scoring.py`)*

**Respaldo de los pesos:** ⚠️ *Heurístico.* La ponderación 40/35/25 es una
decisión de diseño (prioriza la fluidez como objetivo primario del sistema). No
deriva de un estudio; conviene justificarla explícitamente en el informe.

---

## 2. D1 — Fluidez oral (40 %)

Dos criterios; el puntaje se convierte a `score_d1` (0–100).

### 2.1 Velocidad de habla (PPM = palabras por minuto)

| Rango PPM | Valoración | Puntos |
|-----------|------------|--------|
| 80 – 120 | Ideal | 3 |
| 60 – 79 · 121 – 140 | Aceptable (lento/rápido) | 2 |
| < 60 · > 140 | Muy lento / muy rápido | 1 |

**Respaldo:** ✅ *Con base académica.* La velocidad lectora en palabras por
minuto es un indicador estándar de fluidez (Oral Reading Fluency). Referencia:
**Hasbrouck & Tindal (2017), *Oral Reading Fluency Norms*.**
⚠️ *Salvedad:* esas normas varían **por grado escolar**; aquí el rango 80–120 es
fijo para todos. Recomendación: parametrizar el rango por grado.

### 2.2 Bloqueos (pausas largas)

| Bloqueos (pausa > 2 s) | Puntos |
|------------------------|--------|
| 0 | 2 |
| 1 | 1 |
| ≥ 2 | 0 |

- Pausa mínima detectable: **0.5 s**; pausa larga / bloqueo: **2.0 s**
  (`pauses.py`); en el cálculo de PPM se excluye del tiempo de habla toda
  pausa > **1.5 s** (`fluency.py`).

**Respaldo:** ⚠️ *Heurístico.* Que una pausa "silenciosa" larga indique bloqueo o
nerviosismo es razonable en la literatura de disfluencias, pero los umbrales
concretos (0.5 / 1.5 / 2.0 s) son calibraciones propias. Referencia orientativa:
**Bortfeld et al. (2001)** sobre disfluencias del habla espontánea.

---

## 3. D2 — Léxico y coherencia (35 %)

Tres criterios que suman 0–100 (`services/dimension2/feedback.py`).

### 3.1 Muletillas (0–40 pts)

Detección por regex de sonidos de relleno (`eh`, `ah`, `em`, `mmm`…) + lema con
spaCy de muletillas léxicas (`este`, `pues`, `o sea`, `bueno`, `entonces`…).

| Nº de muletillas | Puntos |
|------------------|--------|
| 0 – 1 | 40 |
| 2 – 4 | 25 |
| 5 – 8 | 10 |
| 9 + | 0 |

**Respaldo:** ✅ *Criterio reconocido* (las muletillas / *filled pauses* son un
marcador de fluidez). ⚠️ Los cortes numéricos son heurísticos. *Mejora sugerida:*
puntuar por **tasa** (muletillas / total de palabras) en vez de conteo absoluto,
para no penalizar discursos largos.

### 3.2 Riqueza léxica — TTR (Type-Token Ratio) (0–35 pts)

TTR = palabras únicas / total de palabras (sobre lemas con contenido).

| TTR | Puntos |
|-----|--------|
| > 0.50 | 35 |
| 0.30 – 0.50 | 20 |
| ≤ 0.30 | 5 |

**Respaldo:** ✅ *Con base académica.* El TTR es una medida clásica de diversidad
léxica. Referencias: **Templin (1957)**, **Johnson (1944)**.
⚠️ *Limitación conocida:* el TTR **depende de la longitud** del texto (a más
palabras, menor TTR), lo que lo hace inestable entre grabaciones de distinta
duración. Medidas más robustas: **MTLD** o **VOCD/HD-D** (McCarthy & Jarvis, 2010).

### 3.3 Coherencia semántica (0–25 pts)

Similitud coseno entre oraciones consecutivas usando embeddings de **BETO**
(BERT en español). Si el texto tiene < 2 oraciones, se asigna un valor neutral.

| Método | Umbral "bueno" | Umbral "regular" | Puntos (bueno/regular/bajo) |
|--------|----------------|------------------|-----------------------------|
| BETO (semántico) | > 0.86 | > 0.79 | 25 / 15 / 5 |
| Jaccard (fallback) | > 0.35 | > 0.15 | 25 / 15 / 5 |
| Texto corto (< 2 oraciones) | — | — | 20 (neutral) |

**Respaldo:** ✅ *Con base académica.* Medir coherencia como similitud entre
segmentos de texto es un enfoque establecido (**Foltz, Kintsch & Landauer,
1998**, coherencia vía LSA). BETO: **Cañete et al. (2020), *Spanish Pre-Trained
BERT Model*.**
⚠️ Los umbrales (0.86 / 0.79 para BETO) son calibraciones empíricas propias.

---

## 4. D3 — Expresividad vocal (25 %)

Tres criterios acústicos (Praat / parselmouth) que suman 0–100
(`services/dimension3/acoustic.py`). Usa las métricas prosódicas calculadas en
`prosody.py`.

### 4.1 Variación tonal (0–40 pts)

Coeficiente de variación de la frecuencia fundamental: **CV = f0_std / f0_mean**.

| CV de F0 | Interpretación | Puntos (aprox.) |
|----------|----------------|-----------------|
| ≈ 0.35 | Voz expresiva | 40 (máx.) |
| ≈ 0.10 | Poco expresiva | ~11 |
| ≈ 0.00 | Monótona | 0 |

*(Fórmula: `pts = min(40, CV · 114.3)`.)*

**Respaldo:** ✅ *Con base fonética* (la variación de F0 se asocia a
expresividad/entonación). ⚠️ El punto de anclaje CV=0.35→40 pts es heurístico.

### 4.2 Calidad de voz — HNR (0–30 pts)

HNR = *Harmonics-to-Noise Ratio* (relación armónicos/ruido, en dB).

| HNR | Interpretación | Puntos |
|-----|----------------|--------|
| ≥ 25 dB | Voz limpia y clara | 30 (máx.) |
| ~5 dB | Voz ruidosa / ronca | ~6 |
| ≤ 0 dB | — | 0 |

*(Fórmula: `pts = min(30, HNR/25 · 30)`.)*

**Respaldo:** ✅ *Con base clínica.* HNR, jitter y shimmer son medidas estándar de
calidad vocal. Referencias: **Boersma & Weenink (Praat)**, literatura de
fonación (jitter/shimmer/HNR). ⚠️ El umbral 25 dB→máximo es una calibración.

### 4.3 Volumen — intensidad (0–30 pts)

| Intensidad (dB) | Interpretación | Puntos |
|-----------------|----------------|--------|
| 55 – 75 | Proyección adecuada de aula | 30 |
| 45 – 55 · 75 – 85 | Aceptable | 15 |
| < 45 · > 85 | Muy suave / gritando | 5 |
| Sin datos | Neutro | 10 |

**Respaldo:** ⚠️ *Heurístico.* El rango 55–75 dB "de voz de niño en aula" es una
estimación de diseño, sensible además a la distancia al micrófono y a la
ganancia de grabación (no es dB SPL calibrado).

---

## 5. Conversión final a estrellas y niveles

El `score_global` se traduce a un nivel de 1–5 estrellas (`services/scoring.py`):

| Score global | Nivel | Estrellas |
|--------------|-------|-----------|
| ≥ 85 | Sobresaliente | 5 ⭐ |
| 70 – 84 | Bueno | 4 ⭐ |
| 50 – 69 | En desarrollo | 3 ⭐ |
| 30 – 49 | Necesita apoyo | 2 ⭐ |
| < 30 | Inicio | 1 ⭐ |

**Respaldo:** ⚠️ *Heurístico.* Cortes de diseño para comunicar el resultado de
forma amigable a niños de primaria.

---

## 6. Validación de sesión (guard de contenido mínimo)

Antes de puntuar, una grabación debe superar un mínimo para no inflar el score
con valores por defecto (`services/validation.py`):

- **≥ 10 palabras** transcritas **y**
- **≥ 5 s** de habla efectiva.

Si no los cumple, la sesión se marca inválida y **no se puntúa ni se guarda**.

**Respaldo:** ⚠️ *Heurístico*, pero es una buena práctica de robustez (evita
puntuar silencio/ruido).

---

## 7. Resumen: qué necesita sustento

| Criterio | Estado |
|----------|--------|
| PPM (velocidad lectora) | ✅ Con base — *parametrizar por grado* |
| TTR (riqueza léxica) | ✅ Con base — *considerar MTLD por robustez* |
| Coherencia (BETO / similitud) | ✅ Con base — *umbrales por calibrar* |
| HNR / variación tonal (acústica) | ✅ Con base — *anclajes por calibrar* |
| Pesos 40/35/25 | ⚠️ Heurístico — justificar en informe |
| Umbrales de pausas (0.5/1.5/2 s) | ⚠️ Heurístico |
| Cortes de muletillas / TTR / coherencia | ⚠️ Heurístico |
| Rango de volumen 55–75 dB | ⚠️ Heurístico — no calibrado a SPL |
| Cortes de estrellas/niveles | ⚠️ Heurístico |

**Recomendación general para el informe:** para cada umbral ⚠️, o bien citar una
fuente, o bien **validarlo empíricamente** con un conjunto de audios reales de
niños (etiquetados por un docente) y ajustar los cortes a esos datos. Eso
convierte las heurísticas en criterios defendibles ante un jurado.

> *Nota sobre las referencias:* las fuentes citadas provienen del conocimiento
> del dominio y deben **verificarse y formatearse** según la norma de citación
> del informe (APA) antes de incluirlas.
