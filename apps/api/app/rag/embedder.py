"""Embeddings locales con BAAI/bge-m3 (1024 dims, multilingüe)."""
import logging
from functools import lru_cache
from typing import Any

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    from app.config import get_settings
    settings = get_settings()
    log.info(f"Cargando modelo de embeddings: {settings.embedding_model}")
    return SentenceTransformer(settings.embedding_model)


def embed(text: str) -> list[float]:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()
