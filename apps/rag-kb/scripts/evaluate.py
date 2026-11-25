"""
Evaluación del recall del índice RAG — Sistema conversacional UPLA Admisión.

Ejecuta las consultas del golden_eval.jsonl contra el vector store y mide:
- Recall@k: proporción de consultas cuyo chunk esperado aparece en los top-k resultados.
- Mean Reciprocal Rank (MRR): calidad del ordenamiento.
- Faithfulness por citación: coincidencia de la cita exigida en el resultado top.

Uso:
    python evaluate.py --k 5 --store pgvector
    python evaluate.py --k 3 --store qdrant --export results.jsonl

El reporte se imprime en stdout (tabla) y, con --export, se escribe en JSONL.
"""

import argparse
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import statistics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def embed_query(text: str, provider: str = "openai") -> List[float]:
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
        return resp.data[0].embedding
    else:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        return model.encode([text], normalize_embeddings=True).tolist()[0]


def search_pgvector(embedding: List[float], k: int, conn_str: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    import psycopg2
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    where_clauses = []
    params = [embedding]
    if filters:
        for key, value in filters.items():
            where_clauses.append(f"metadata->>'{key}' = %s")
            params.append(value)
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cur.execute(f"""
        SELECT id, text, metadata, 1 - (embedding <=> %s::vector) AS score
        FROM kb_chunks
        {where_sql}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, params + [embedding, k])

    results = [
        {"id": row[0], "text": row[1], "metadata": row[2], "score": float(row[3])}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return results


def search_qdrant(embedding: List[float], k: int, url: str, collection: str = "upla_admision_kb", filters: Dict = None):
    from qdrant_client import QdrantClient
    client = QdrantClient(url=url)
    hits = client.search(
        collection_name=collection,
        query_vector=embedding,
        limit=k,
    )
    return [
        {"id": hit.payload["id"], "text": hit.payload["text"], "metadata": hit.payload, "score": hit.score}
        for hit in hits
    ]


def evaluate_query(query: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evalúa una consulta contra los resultados recuperados."""
    expected_ids = set(query["expected_chunks"])
    retrieved_ids = [r["id"] for r in results]

    # Recall@k
    hits_at_k = [cid for cid in retrieved_ids if cid in expected_ids]
    recall = len(hits_at_k) / len(expected_ids) if expected_ids else 0

    # Reciprocal Rank: posición del primer hit (1-indexed)
    rr = 0
    for i, cid in enumerate(retrieved_ids, 1):
        if cid in expected_ids:
            rr = 1 / i
            break

    # Faithfulness: ¿el top-1 cita el artículo exigido?
    top_citation = results[0]["metadata"].get("citation", "") if results else ""
    citation_match = query["citation_required"] in top_citation if query.get("citation_required") else None

    return {
        "query_id": query["query_id"],
        "query": query["query"],
        "difficulty": query.get("difficulty", "n/a"),
        "expected_ids": list(expected_ids),
        "retrieved_ids": retrieved_ids,
        "recall": recall,
        "reciprocal_rank": rr,
        "citation_match": citation_match,
        "hit": rr > 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5, help="Top-k a recuperar")
    parser.add_argument("--store", choices=["pgvector", "qdrant"], default="pgvector")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai")
    parser.add_argument("--eval-file", type=Path,
                        default=Path(__file__).parent.parent / "data" / "golden_eval.jsonl")
    parser.add_argument("--export", type=Path, help="Exportar resultados a JSONL")
    args = parser.parse_args()

    # Cargar golden set
    with args.eval_file.open() as f:
        queries = [json.loads(line) for line in f if line.strip()]
    log.info(f"Evaluando con {len(queries)} consultas (k={args.k})")

    results = []
    for q in queries:
        emb = embed_query(q["query"], args.provider)
        if args.store == "pgvector":
            hits = search_pgvector(emb, args.k, os.environ["PGVECTOR_CONN"])
        else:
            hits = search_qdrant(emb, args.k, os.environ.get("QDRANT_URL", "http://localhost:6333"))
        results.append(evaluate_query(q, hits))

    # Agregados
    recall_values = [r["recall"] for r in results]
    rr_values = [r["reciprocal_rank"] for r in results]
    citation_matches = [r["citation_match"] for r in results if r["citation_match"] is not None]

    print(f"\n{'='*70}")
    print(f"RESULTADOS DE EVALUACIÓN (k={args.k})")
    print(f"{'='*70}")
    print(f"Consultas evaluadas:    {len(results)}")
    print(f"Hit rate (recall > 0):  {sum(1 for r in results if r['hit']) / len(results):.2%}")
    print(f"Recall promedio:        {statistics.mean(recall_values):.3f}")
    print(f"MRR:                    {statistics.mean(rr_values):.3f}")
    if citation_matches:
        print(f"Citación top-1 OK:      {sum(citation_matches) / len(citation_matches):.2%}")

    # Por dificultad
    print(f"\nPor dificultad:")
    for diff in ("easy", "medium", "hard"):
        subset = [r for r in results if r["difficulty"] == diff]
        if subset:
            print(f"  {diff:7}  n={len(subset)}  recall={statistics.mean(r['recall'] for r in subset):.3f}  MRR={statistics.mean(r['reciprocal_rank'] for r in subset):.3f}")

    # Fallos
    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\nConsultas sin hit ({len(misses)}):")
        for r in misses:
            print(f"  {r['query_id']}: {r['query'][:70]}")

    # Exportación
    if args.export:
        with args.export.open("w") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        log.info(f"Resultados exportados a {args.export}")


if __name__ == "__main__":
    main()
