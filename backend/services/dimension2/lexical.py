"""
Dimensión 2 — Análisis léxico y coherencia
  · detect_muletillas()  → muletillas verbales (spaCy lemas + regex de relleno)
  · calc_ttr()           → Type-Token Ratio sobre lemas (riqueza léxica)
  · calc_coherencia()    → coherencia entre oraciones con BETO (cosine similarity)

Usa spaCy + BETO cuando están disponibles. Si no cargan, hace fallback
automático a métodos clásicos (split + Jaccard) para no romper nunca.
"""
import re
import unicodedata

from services.nlp_models import get_spacy, beto_embedding

# ─── Muletillas (relleno) ─────────────────────────────────────────────────────
# Patrones regex para sonidos elongados que spaCy no tokeniza como palabra real
MULETILLAS_REGEX = [
    (r'\be+h+\b',     "eh"),
    (r'\ba+h+\b',     "ah"),
    (r'\be+m+\b',     "em"),
    (r'\bu+m+\b',     "um"),
    (r'\bm{2,}\b',    "mm"),
    (r'\best[e]{2,}\b', "esteee"),
]
# Lemas/palabras de relleno (se detectan por lema con spaCy)
MULETILLAS_LEMAS = {
    "este", "eso", "pues", "bueno", "osea", "entonces",
    "digamos", "claro", "verdad", "tipo", "o_sea",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", texto)


def _split_oraciones(texto: str) -> list[str]:
    partes = re.split(r"[.!?]+", texto)
    return [o.strip() for o in partes if len(o.strip()) > 8]


# ══════════════════════════════════════════════════════════════════════════════
# 1. MULETILLAS
# ══════════════════════════════════════════════════════════════════════════════
def detect_muletillas(transcripcion: str) -> dict:
    nlp = get_spacy()
    texto_norm = _normalizar(transcripcion)
    total_tokens = len(texto_norm.split()) or 1

    por_tipo: dict[str, int] = {}

    # 1a. Sonidos de relleno elongados (regex sobre texto normalizado)
    for patron, etiqueta in MULETILLAS_REGEX:
        n = len(re.findall(patron, texto_norm))
        if n:
            por_tipo[etiqueta] = por_tipo.get(etiqueta, 0) + n

    # 1b. Muletillas léxicas por lema (spaCy) o por palabra (fallback)
    if nlp is not None:
        doc = nlp(transcripcion.lower())
        for token in doc:
            lema = token.lemma_.lower().strip()
            if lema in MULETILLAS_LEMAS:
                por_tipo[lema] = por_tipo.get(lema, 0) + 1
        metodo = "spacy"
    else:
        palabras = texto_norm.split()
        for p in palabras:
            if p in MULETILLAS_LEMAS:
                por_tipo[p] = por_tipo.get(p, 0) + 1
        metodo = "fallback"

    count = sum(por_tipo.values())
    tasa = round(count / total_tokens * 100, 2)

    return {
        "muletillas_count": count,
        "muletillas_tasa": tasa,
        "muletillas_list": list(por_tipo.keys()),
        "por_tipo": por_tipo,
        "metodo": metodo,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. RIQUEZA LÉXICA (TTR sobre lemas)
# ══════════════════════════════════════════════════════════════════════════════
def calc_ttr(transcripcion: str) -> dict:
    nlp = get_spacy()

    if nlp is not None:
        doc = nlp(transcripcion.lower())
        # Solo palabras con contenido: sin stopwords, sin puntuación, alfabéticas
        lemas = [t.lemma_.lower() for t in doc
                 if t.is_alpha and not t.is_stop and len(t.lemma_) >= 2]
        metodo = "spacy"
    else:
        from collections import Counter  # noqa
        STOP = {"el","la","los","las","un","una","y","o","de","que","en","a",
                "me","mi","tu","su","se","es","fue","muy","con","por","para"}
        lemas = [t for t in _normalizar(transcripcion).split()
                 if t not in STOP and len(t) >= 2]
        metodo = "fallback"

    if not lemas:
        return {"word_count": 0, "unique_words": 0, "ttr_score": 0.0, "metodo": metodo}

    types = set(lemas)
    ttr = len(types) / len(lemas)
    return {
        "word_count": len(lemas),
        "unique_words": len(types),
        "ttr_score": round(ttr, 3),
        "metodo": metodo,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. COHERENCIA SEMÁNTICA (BETO embeddings + cosine similarity)
# ══════════════════════════════════════════════════════════════════════════════
def _coherencia_jaccard(oraciones: list[str]) -> list[float]:
    """Fallback clásico: solapamiento de palabras (Jaccard)."""
    def palabras(o):
        return {w for w in _normalizar(o).split() if len(w) >= 2}
    sims = []
    for i in range(len(oraciones) - 1):
        a, b = palabras(oraciones[i]), palabras(oraciones[i + 1])
        union = a | b
        sims.append(len(a & b) / len(union) if union else 0.0)
    return sims


def calc_coherencia(transcripcion: str) -> dict:
    oraciones = _split_oraciones(transcripcion)

    if len(oraciones) < 2:
        return {
            "coherencia_score": 0.80,  # neutral alto: texto corto, no penalizar
            "oraciones_analizadas": len(oraciones),
            "metodo": "n/a",
            "nota": "texto demasiado corto para medir coherencia",
        }

    # Intentar con BETO (semántico)
    import torch
    import torch.nn.functional as F

    embeddings = [beto_embedding(o) for o in oraciones]
    usar_beto = all(e is not None for e in embeddings)

    if usar_beto:
        sims = []
        for i in range(len(embeddings) - 1):
            sim = F.cosine_similarity(embeddings[i], embeddings[i + 1]).item()
            sims.append(round(sim, 3))
        metodo = "beto"
    else:
        sims = [round(s, 3) for s in _coherencia_jaccard(oraciones)]
        metodo = "jaccard"

    score = round(sum(sims) / len(sims), 3) if sims else 0.0
    return {
        "coherencia_score": score,
        "oraciones_analizadas": len(oraciones),
        "similitudes": sims,
        "metodo": metodo,
    }
