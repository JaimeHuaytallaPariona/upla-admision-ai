"""Ingesta de chunks al índice pgvector (invocado al arrancar si está vacío)."""
import hashlib
import json
import logging
from pathlib import Path

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.rag.embedder import embed_batch

log = logging.getLogger(__name__)

# El pipeline canónico vive en apps/rag-kb/scripts/ingest.py.
# Este módulo lo consume en forma de librería al arrancar.

import os
_env_kb = os.getenv("KB_DATA_DIR")
if _env_kb:
    KB_DATA_DIR = Path(_env_kb)
else:
    # Local (fuera de docker): sube hasta la raíz del repo y entra a apps/rag-kb/data
    _here = Path(__file__).resolve()
    _candidates = [
        Path("/rag-kb/data"),  # montaje en docker
        _here.parents[3] / "rag-kb" / "data",  # /app/rag-kb (si el volumen se monta ahí)
        _here.parents[4] / "apps" / "rag-kb" / "data",  # repo root/apps/rag-kb/data
        _here.parents[5] / "apps" / "rag-kb" / "data",
    ]
    KB_DATA_DIR = next((c for c in _candidates if c.exists()), _candidates[0])


def _normalize_for_embedding(chunk: dict) -> str:
    parts = []
    if chunk.get("chapter"):
        parts.append(f"[Capítulo: {chunk['chapter']}]")
    if chunk.get("article"):
        parts.append(f"[Artículo: {chunk['article']}]")
    if chunk.get("topic"):
        parts.append(f"[Tema: {chunk['topic']}]")
    parts.append(chunk.get("text", ""))
    return " ".join(parts)


def _content_hash(chunk: dict) -> str:
    core = {"id": chunk["id"], "text": chunk["text"], "citation": chunk.get("citation", "")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def count_chunks(db: Session) -> int:
    row = db.execute(sql_text("SELECT COUNT(*) FROM kb_chunks")).fetchone()
    return int(row[0]) if row else 0


def bootstrap_index_if_empty(db: Session) -> int:
    """Si el índice está vacío, lo llena con los JSONL de rag-kb/data. Retorna chunks indexados."""
    existing = count_chunks(db)
    if existing > 0:
        log.info(f"Índice ya contiene {existing} chunks; se omite bootstrap.")
        return 0

    files = sorted(KB_DATA_DIR.glob("*.jsonl"))
    files = [f for f in files if f.name != "golden_eval.jsonl"]  # golden no va al índice
    if not files:
        log.warning(f"No se encontraron JSONL en {KB_DATA_DIR}")
        return 0

    chunks: list[dict] = []
    for f in files:
        count = 0
        for c in _iter_jsonl(f):
            chunks.append(c)
            count += 1
        log.info(f"  {f.name}: {count} chunks cargados")

    log.info(f"Generando embeddings para {len(chunks)} chunks…")
    texts = [_normalize_for_embedding(c) for c in chunks]
    embs = embed_batch(texts)

    for c, e in zip(chunks, embs):
        db.execute(
            sql_text("""
                INSERT INTO kb_chunks (id, text, embedding, metadata, content_hash)
                VALUES (:id, :text, CAST(:emb AS vector), CAST(:meta AS jsonb), :hash)
                ON CONFLICT (id) DO NOTHING;
            """),
            {
                "id": c["id"],
                "text": c["text"],
                "emb": str(e),
                "meta": json.dumps(c),
                "hash": _content_hash(c),
            },
        )
    db.commit()
    log.info(f"Bootstrap completado: {len(chunks)} chunks indexados.")

    # Índice HNSW para producción; ivfflat necesita datos primero
    try:
        db.execute(sql_text(
            "CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding "
            "ON kb_chunks USING hnsw (embedding vector_cosine_ops)"
        ))
        db.commit()
    except Exception as e:
        log.warning(f"No se pudo crear índice HNSW: {e}")

    return len(chunks)
