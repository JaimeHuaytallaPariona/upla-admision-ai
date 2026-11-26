"""Ingesta de chunks al indice pgvector (invocado al arrancar si esta vacio)."""
import hashlib
import json
import logging
import os
from pathlib import Path

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.rag.embedder import embed_batch

log = logging.getLogger(__name__)


def _resolve_kb_dir() -> Path:
    env = os.getenv("KB_DATA_DIR")
    if env:
        return Path(env)
    _here = Path(__file__).resolve()
    candidates = [Path("/rag-kb/data")]
    for n in (3, 4, 5):
        try:
            candidates.append(_here.parents[n] / "rag-kb" / "data")
            candidates.append(_here.parents[n] / "apps" / "rag-kb" / "data")
        except IndexError:
            continue
    for c in candidates:
        if c.exists():
            return c
    return Path("/rag-kb/data")


KB_DATA_DIR = _resolve_kb_dir()


def _to_chunk(raw: dict) -> dict | None:
    """Normaliza un registro JSONL a un chunk indexable (con id, text, citation)."""
    if "id" in raw and "text" in raw:
        return raw

    if "modalidad_id" in raw:
        mid = str(raw["modalidad_id"])
        parts = [f"Modalidad: {raw.get('nombre', mid)}."]
        if raw.get("articulo_fuente"):
            parts.append(f"Fuente normativa: {raw['articulo_fuente']}.")
        if raw.get("aplica_a"):
            parts.append(f"Aplica a: {raw['aplica_a']}.")
        if raw.get("requisitos_base"):
            parts.append(f"Requisitos base: {'; '.join(str(x) for x in raw['requisitos_base'])}.")
        if raw.get("requisitos_especificos"):
            parts.append(f"Requisitos especificos: {'; '.join(str(x) for x in raw['requisitos_especificos'])}.")
        if raw.get("excepciones_programa"):
            parts.append(f"Excepciones por programa: {raw['excepciones_programa']}.")
        if raw.get("ingreso_directo") is not None:
            parts.append(f"Ingreso directo: {'si' if raw['ingreso_directo'] else 'no'}.")
        if raw.get("beneficios_economicos"):
            parts.append(f"Beneficios economicos: {raw['beneficios_economicos']}.")
        if raw.get("notas"):
            parts.append(f"Notas: {raw['notas']}.")
        text = " ".join(parts)
        return {
            "id": f"MOD-{mid.upper()}",
            "text": text,
            "citation": f"Catalogo oficial de modalidades UPLA - {raw.get('nombre', mid)}",
            "source": "Catalogo de modalidades UPLA",
            "source_type": "catalogo_modalidad",
            "topic": "modalidad",
            "modalidades_aplicables": [mid],
            "canales_aplicables": ["todos"],
            "sensitivity": "public",
            "version": "1.0",
        }

    if "canal_id" in raw:
        cid = str(raw["canal_id"])
        parts = [f"Canal {cid}."]
        if raw.get("carreras"):
            parts.append(f"Carreras del canal: {', '.join(str(x) for x in raw['carreras'])}.")
        if raw.get("asignaturas"):
            asigs = []
            for a in raw["asignaturas"]:
                if isinstance(a, dict):
                    asigs.append(f"{a.get('nombre','?')} (ponderacion {a.get('ponderacion','?')})")
                else:
                    asigs.append(str(a))
            parts.append(f"Composicion del examen: {', '.join(asigs)}.")
        if raw.get("duracion_examen"):
            parts.append(f"Duracion del examen: {raw['duracion_examen']}.")
        if raw.get("articulo_fuente"):
            parts.append(f"Fuente normativa: {raw['articulo_fuente']}.")
        text = " ".join(parts)
        return {
            "id": f"CAN-{cid.upper()}",
            "text": text,
            "citation": f"Catalogo oficial de canales UPLA - Canal {cid}",
            "source": "Catalogo de canales UPLA",
            "source_type": "catalogo_canal",
            "topic": "canal_examen",
            "modalidades_aplicables": ["todas"],
            "canales_aplicables": [cid],
            "sensitivity": "public",
            "version": "1.0",
        }

    return None


def _normalize_for_embedding(chunk: dict) -> str:
    parts = []
    if chunk.get("chapter"):
        parts.append(f"[Capitulo: {chunk['chapter']}]")
    if chunk.get("article"):
        parts.append(f"[Articulo: {chunk['article']}]")
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
    existing = count_chunks(db)
    if existing > 0:
        log.info(f"Indice ya contiene {existing} chunks; se omite bootstrap.")
        return 0

    files = sorted(KB_DATA_DIR.glob("*.jsonl"))
    files = [f for f in files if f.name != "golden_eval.jsonl"]
    if not files:
        log.warning(f"No se encontraron JSONL en {KB_DATA_DIR}")
        return 0

    chunks: list[dict] = []
    for f in files:
        count = 0
        for raw in _iter_jsonl(f):
            chunk = _to_chunk(raw)
            if chunk:
                chunks.append(chunk)
                count += 1
        log.info(f"  {f.name}: {count} chunks cargados")

    log.info(f"Generando embeddings para {len(chunks)} chunks...")
    texts = [_normalize_for_embedding(c) for c in chunks]
    embs = embed_batch(texts)

    for c, e in zip(chunks, embs):
        db.execute(
            sql_text("""
                INSERT INTO kb_chunks (id, text, embedding, metadata, content_hash, indexed_at)
                VALUES (:id, :text, CAST(:emb AS vector), CAST(:meta AS jsonb), :hash, NOW())
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

    try:
        db.execute(sql_text(
            "CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding "
            "ON kb_chunks USING hnsw (embedding vector_cosine_ops)"
        ))
        db.commit()
    except Exception as e:
        log.warning(f"No se pudo crear indice HNSW: {e}")

    return len(chunks)

