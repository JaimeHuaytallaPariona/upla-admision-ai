"""
Pipeline de ingesta de la base de conocimiento RAG — Sistema conversacional UPLA Admisión.

Carga los chunks desde los archivos JSONL, genera embeddings y los indexa
en un vector store (pgvector o Qdrant).

Uso:
    python ingest.py --source reglamento_chunks.jsonl --store pgvector
    python ingest.py --source modalidades.jsonl --store pgvector
    python ingest.py --all --store pgvector

Dependencias:
    pip install openai psycopg2-binary qdrant-client sentence-transformers

Variables de entorno:
    OPENAI_API_KEY        — si se usa el proveedor OpenAI de embeddings
    PGVECTOR_CONN         — cadena de conexión PostgreSQL (postgresql://user:pass@host/db)
    QDRANT_URL            — URL del servidor Qdrant (http://host:6333)
    EMBEDDING_MODEL       — por defecto 'text-embedding-3-small' (OpenAI) o 'BAAI/bge-m3' (local)
"""

import argparse
import json
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Iterator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536  # text-embedding-3-small; BAAI/bge-m3 es 1024


def iter_chunks(path: Path) -> Iterator[Dict[str, Any]]:
    """Itera por los chunks de un archivo JSONL."""
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.error(f"JSON inválido en {path.name}:{line_num}: {e}")
                raise


def normalize_chunk_for_embedding(chunk: Dict[str, Any]) -> str:
    """
    Prepara el texto que entra al embedding model.
    Estrategia: prepender metadata semánticamente relevante al texto para
    que el embedding capture no solo el contenido sino el contexto normativo.
    """
    parts = []
    if chunk.get("chapter"):
        parts.append(f"[Capítulo: {chunk['chapter']}]")
    if chunk.get("article"):
        parts.append(f"[Artículo: {chunk['article']}]")
    if chunk.get("topic"):
        parts.append(f"[Tema: {chunk['topic']}]")
    if chunk.get("modalidades_aplicables"):
        parts.append(f"[Modalidades: {', '.join(chunk['modalidades_aplicables'])}]")
    if chunk.get("canales_aplicables"):
        parts.append(f"[Canales: {', '.join(chunk['canales_aplicables'])}]")
    parts.append(chunk.get("text", ""))
    return " ".join(parts)


def compute_content_hash(chunk: Dict[str, Any]) -> str:
    """Hash estable del contenido semántico. Permite detectar cambios en re-ingesta."""
    core = {
        "id": chunk["id"],
        "text": chunk["text"],
        "citation": chunk["citation"],
        "version": chunk.get("version", "1.0"),
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def generate_embeddings_openai(texts: List[str]) -> List[List[float]]:
    """Genera embeddings con OpenAI."""
    from openai import OpenAI
    client = OpenAI()
    resp = client.embeddings.create(
        model=DEFAULT_EMBEDDING_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def generate_embeddings_local(texts: List[str]) -> List[List[float]]:
    """Genera embeddings con modelo local (sentence-transformers)."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    return model.encode(texts, normalize_embeddings=True).tolist()


def upsert_pgvector(chunks: List[Dict[str, Any]], embeddings: List[List[float]], conn_str: str):
    """Inserta o actualiza los chunks en PostgreSQL con pgvector."""
    import psycopg2
    from psycopg2.extras import Json

    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kb_chunks (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            embedding vector(%s),
            metadata JSONB NOT NULL,
            content_hash TEXT NOT NULL,
            indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding
            ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);
        CREATE INDEX IF NOT EXISTS idx_kb_chunks_metadata
            ON kb_chunks USING gin (metadata);
    """, (EMBEDDING_DIM,))

    for chunk, emb in zip(chunks, embeddings):
        cur.execute("""
            INSERT INTO kb_chunks (id, text, embedding, metadata, content_hash)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    content_hash = EXCLUDED.content_hash,
                    indexed_at = NOW()
                WHERE kb_chunks.content_hash != EXCLUDED.content_hash;
        """, (chunk["id"], chunk["text"], emb, Json(chunk), compute_content_hash(chunk)))

    conn.commit()
    cur.close()
    conn.close()


def upsert_qdrant(chunks: List[Dict[str, Any]], embeddings: List[List[float]], url: str, collection: str = "upla_admision_kb"):
    """Inserta o actualiza los chunks en Qdrant."""
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct

    client = QdrantClient(url=url)
    try:
        client.get_collection(collection)
    except Exception:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=hash_id(chunk["id"]),
            vector=emb,
            payload={**chunk, "content_hash": compute_content_hash(chunk)},
        )
        for chunk, emb in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=collection, points=points)


def hash_id(string_id: str) -> int:
    """Convierte un ID de string a entero (requerido por Qdrant)."""
    return int(hashlib.md5(string_id.encode()).hexdigest()[:15], 16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="Archivo JSONL de chunks a ingerir")
    parser.add_argument("--all", action="store_true", help="Ingerir todos los archivos de data/")
    parser.add_argument("--store", choices=["pgvector", "qdrant"], default="pgvector")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true", help="Validar sin indexar")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    sources = (
        [data_dir / "reglamento_chunks.jsonl", data_dir / "modalidades.jsonl", data_dir / "canales.jsonl"]
        if args.all else [args.source]
    )

    embed_fn = generate_embeddings_openai if args.provider == "openai" else generate_embeddings_local

    for src in sources:
        if not src or not src.exists():
            log.error(f"No existe: {src}")
            continue
        log.info(f"Ingiriendo {src.name}…")

        chunks = list(iter_chunks(src))
        log.info(f"  {len(chunks)} chunks encontrados")

        if args.dry_run:
            log.info("  (dry-run: sin indexar)")
            continue

        # Procesar en batches
        for i in range(0, len(chunks), args.batch_size):
            batch = chunks[i:i + args.batch_size]
            texts = [normalize_chunk_for_embedding(c) for c in batch]
            embs = embed_fn(texts)

            if args.store == "pgvector":
                conn_str = os.environ["PGVECTOR_CONN"]
                upsert_pgvector(batch, embs, conn_str)
            elif args.store == "qdrant":
                qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
                upsert_qdrant(batch, embs, qdrant_url)

            log.info(f"  batch {i // args.batch_size + 1}: {len(batch)} chunks indexados")

    log.info("Ingesta completada.")


if __name__ == "__main__":
    main()
