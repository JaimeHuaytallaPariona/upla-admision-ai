"""Embeddings locales con BAAI/bge-m3 via fastembed (ONNX, sin PyTorch)."""
import logging
from functools import lru_cache

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding
    from app.config import get_settings
    settings = get_settings()
    log.info(f"Cargando modelo de embeddings: {settings.embedding_model}")
    return TextEmbedding(model_name=settings.embedding_model)


def embed(text: str) -> list[float]:
    model = _get_model()
    return list(next(model.embed([text])))


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return [list(e) for e in model.embed(texts)]
