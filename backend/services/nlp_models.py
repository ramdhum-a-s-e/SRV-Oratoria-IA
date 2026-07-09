"""
Carga lazy (singleton) de los modelos NLP para la Dimensión 2:
  · spaCy es_core_news_lg  → tokenización, lematización, POS
  · BETO (bert-base-spanish-wwm-cased) → embeddings para coherencia semántica

Los modelos se cargan una sola vez y se reutilizan. Si la carga falla
(p. ej. el modelo no está descargado), se devuelve None y el código que
los usa hace fallback a métodos clásicos (regex / Jaccard).
"""
import os

# Ruta local donde se descargó BETO (ver models_cache/beto).
# En producción, si la carpeta no existe, se intenta el identificador de HuggingFace.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BETO_LOCAL  = os.path.join(_BACKEND_DIR, "models_cache", "beto")
_BETO_HF_ID  = "dccuchile/bert-base-spanish-wwm-cased"
# Se intentan en orden de preferencia (mayor calidad primero). Se usa el primero
# que esté instalado, así el sistema NUNCA cae silenciosamente al fallback de
# regex/split solo por un nombre de modelo que no coincide con lo instalado.
_SPACY_MODELS = ["es_core_news_lg", "es_core_news_md", "es_core_news_sm"]

_nlp = None            # spaCy pipeline
_beto_tok = None       # BETO tokenizer
_beto_model = None     # BETO model
_spacy_tried = False
_beto_tried = False


def get_spacy():
    """Devuelve el pipeline de spaCy, o None si no se pudo cargar."""
    global _nlp, _spacy_tried
    if _nlp is None and not _spacy_tried:
        _spacy_tried = True
        import spacy
        for modelo in _SPACY_MODELS:
            try:
                print(f"[SRV] Cargando spaCy '{modelo}'...")
                # Desactivamos componentes que no usamos (ner, parser) para acelerar
                _nlp = spacy.load(modelo, disable=["ner", "parser"])
                print(f"[SRV] spaCy '{modelo}' cargado OK")
                break
            except Exception as e:
                print(f"[SRV] No se pudo cargar spaCy '{modelo}' ({e}).")
        if _nlp is None:
            print("[SRV] Ningún modelo spaCy disponible. Fallback a regex/split.")
    return _nlp


def get_beto():
    """Devuelve (tokenizer, model) de BETO en modo eval, o (None, None) si falla."""
    global _beto_tok, _beto_model, _beto_tried
    if _beto_model is None and not _beto_tried:
        _beto_tried = True
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            ruta = _BETO_LOCAL if os.path.isdir(_BETO_LOCAL) else _BETO_HF_ID
            print(f"[SRV] Cargando BETO desde '{ruta}'...")
            _beto_tok = AutoTokenizer.from_pretrained(ruta)
            _beto_model = AutoModel.from_pretrained(ruta)
            _beto_model.eval()
            print("[SRV] BETO cargado OK")
        except Exception as e:
            print(f"[SRV] No se pudo cargar BETO ({e}). Fallback a Jaccard.")
            _beto_tok, _beto_model = None, None
    return _beto_tok, _beto_model


def beto_embedding(texto: str):
    """
    Devuelve el embedding (tensor 1xH) de una oración usando mean pooling
    sobre los tokens de BETO (excluye [CLS] y [SEP]). None si BETO no está.
    """
    import torch
    tok, model = get_beto()
    if tok is None or model is None:
        return None
    inputs = tok(texto, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        output = model(**inputs)
    # Mean pooling sobre tokens de contenido (sin [CLS]/[SEP])
    token_embeddings = output.last_hidden_state[:, 1:-1, :]
    if token_embeddings.shape[1] == 0:
        return output.last_hidden_state.mean(dim=1)
    return token_embeddings.mean(dim=1)
