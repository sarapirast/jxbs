"""
Local embedding model
"""
from sentence_transformers import SentenceTransformer

_model = None

QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _model


def embed_text(text: str) -> list[float]:
    """Document-side embedding"""
    return get_model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Document-side batch embedding"""
    return get_model().encode(texts, normalize_embeddings=True, batch_size=32).tolist()


def embed_query(text: str) -> list[float]:
    """Query-side embedding"""
    return get_model().encode(QUERY_INSTRUCTION + text, normalize_embeddings=True).tolist()