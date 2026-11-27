"""
Evaluador CI del índice RAG — UPLA Admisión.

- Carga todos los chunks de los JSONL en `data/`
- Carga el golden set (data/golden_eval.jsonl + data/golden_sgc.jsonl si existe)
- Indexa chunks en memoria con fastembed (mismo modelo que la app)
- Recupera top-k por similitud coseno
- Calcula Hit rate, Recall, MRR, Citation match
- Falla con exit 1 si alguna métrica cae bajo los umbrales definidos

Uso:
    python scripts/evaluate_ci.py --k 5
    python scripts/evaluate_ci.py --k 5 --strict  # exige los umbrales
    python scripts/evaluate_ci.py --k 5 --export results.jsonl

Variables de entorno:
    EMBEDDING_MODEL  (default: BAAI/bge-small-en-v1.5)
    RAG_MIN_HIT      (default: 0.90)
    RAG_MIN_RECALL   (default: 0.80)
    RAG_MIN_MRR      (default: 0.70)
    RAG_MIN_CITATION (default: 0.75)

Dependencias:
    pip install fastembed numpy
"""
import argparse, json, logging, os, sys, statistics
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rag-ci")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DIR = ROOT / "data"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# Umbrales por defecto (configurables por env). Calibrados contra BAAI/bge-small-en-v1.5
# — modelo mayoritariamente anglosajón pero usado por el backend v0.1 y v0.2.
# Son el piso: cada mejora del retriever (reranker, bge-m3 multilingüe, hybrid search)
# debe subirlos.
MIN_HIT = float(os.getenv("RAG_MIN_HIT", "0.85"))
MIN_RECALL = float(os.getenv("RAG_MIN_RECALL", "0.70"))
MIN_MRR = float(os.getenv("RAG_MIN_MRR", "0.65"))
MIN_CITATION = float(os.getenv("RAG_MIN_CITATION", "0.70"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def normalize_for_embedding(chunk: dict) -> str:
    parts = []
    if chunk.get("chapter"):
        parts.append(f"[Capítulo: {chunk['chapter']}]")
    if chunk.get("article"):
        parts.append(f"[Artículo: {chunk['article']}]")
    if chunk.get("topic"):
        parts.append(f"[Tema: {chunk['topic']}]")
    parts.append(chunk.get("text", ""))
    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--strict", action="store_true",
                        help="Devolver exit 1 si alguna métrica cae bajo umbral")
    parser.add_argument("--export", type=Path, help="Exportar resultados a JSONL")
    parser.add_argument("--markdown", type=Path, help="Exportar reporte markdown")
    args = parser.parse_args()

    # Cargar chunks (los JSONL de catálogos — sin campo 'id' — se saltan: no son
    # chunks indexables por sí mismos; el pipeline de ingesta los transforma antes)
    chunks = []
    skipped = 0
    for path in sorted(args.data_dir.glob("*.jsonl")):
        if "golden" in path.name:
            continue
        for c in load_jsonl(path):
            if "id" in c and "text" in c:
                chunks.append(c)
            else:
                skipped += 1
    log.info(f"Chunks cargados: {len(chunks)} desde {args.data_dir} (saltados sin id/text: {skipped})")

    # Cargar golden set (acepta golden_eval.jsonl + golden_sgc.jsonl)
    queries = []
    for path in sorted(args.data_dir.glob("golden*.jsonl")):
        for q in load_jsonl(path):
            queries.append(q)
    log.info(f"Queries golden: {len(queries)}")

    if not chunks or not queries:
        log.error("No hay chunks o queries para evaluar.")
        sys.exit(2)

    # Embedder
    log.info(f"Cargando embedder {EMBEDDING_MODEL}...")
    from fastembed import TextEmbedding
    emb = TextEmbedding(model_name=EMBEDDING_MODEL)

    log.info("Embedding de chunks...")
    chunk_texts = [normalize_for_embedding(c) for c in chunks]
    chunk_embs = np.array(list(emb.embed(chunk_texts)), dtype=np.float32)
    # Normalizar (fastembed ya devuelve normalizados, pero por seguridad)
    norms = np.linalg.norm(chunk_embs, axis=1, keepdims=True)
    chunk_embs = chunk_embs / np.where(norms > 0, norms, 1)
    log.info(f"Matriz de embeddings: {chunk_embs.shape}")

    log.info("Evaluando queries...")
    query_texts = [q["query"] for q in queries]
    query_embs = np.array(list(emb.embed(query_texts)), dtype=np.float32)
    qnorms = np.linalg.norm(query_embs, axis=1, keepdims=True)
    query_embs = query_embs / np.where(qnorms > 0, qnorms, 1)

    # Score matriz: cosine (ya normalizado => dot product)
    scores = query_embs @ chunk_embs.T  # (Q, N)

    results = []
    for qi, q in enumerate(queries):
        row = scores[qi]
        top_idx = np.argsort(-row)[: args.k]
        retrieved = [chunks[i]["id"] for i in top_idx]
        expected = set(q.get("expected_chunks", []))
        hits = [cid for cid in retrieved if cid in expected]
        recall = len(hits) / len(expected) if expected else 0.0
        rr = 0.0
        for i, cid in enumerate(retrieved, 1):
            if cid in expected:
                rr = 1.0 / i
                break
        # Citation
        citation_match = None
        if q.get("citation_required") and top_idx.size > 0:
            top_citation = chunks[top_idx[0]].get("citation", "") or ""
            citation_match = q["citation_required"] in top_citation
        results.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "difficulty": q.get("difficulty", "n/a"),
            "topic_expected": q.get("topic_expected", q.get("intent", "")),
            "sensitivity": q.get("sensitivity", "public"),
            "expected": list(expected),
            "retrieved": retrieved,
            "recall": recall,
            "reciprocal_rank": rr,
            "citation_match": citation_match,
            "hit": rr > 0,
        })

    # Métricas agregadas
    hit_rate = sum(1 for r in results if r["hit"]) / len(results)
    recall_m = statistics.mean(r["recall"] for r in results)
    mrr = statistics.mean(r["reciprocal_rank"] for r in results)
    cits = [r["citation_match"] for r in results if r["citation_match"] is not None]
    citation_rate = (sum(cits) / len(cits)) if cits else None

    print("=" * 72)
    print(f"RESULTADOS RAG CI (k={args.k}) — modelo: {EMBEDDING_MODEL}")
    print("=" * 72)
    print(f"Chunks indexados:       {len(chunks)}")
    print(f"Queries evaluadas:      {len(results)}")
    print(f"Hit rate @ k:           {hit_rate:.2%}   (umbral: {MIN_HIT:.2%})")
    print(f"Recall promedio:        {recall_m:.3f}     (umbral: {MIN_RECALL:.3f})")
    print(f"MRR:                    {mrr:.3f}     (umbral: {MIN_MRR:.3f})")
    if citation_rate is not None:
        print(f"Citation match top-1:   {citation_rate:.2%}   (umbral: {MIN_CITATION:.2%})")
    else:
        print(f"Citation match top-1:   N/A (ningún golden exige citación)")

    # Por dificultad y por tema
    print("\nPor dificultad:")
    for diff in ("easy", "medium", "hard"):
        sub = [r for r in results if r["difficulty"] == diff]
        if sub:
            print(f"  {diff:7}  n={len(sub):3}  hit={sum(1 for r in sub if r['hit'])/len(sub):.0%}  "
                  f"recall={statistics.mean(r['recall'] for r in sub):.3f}  "
                  f"MRR={statistics.mean(r['reciprocal_rank'] for r in sub):.3f}")

    print("\nPor tema (topic_expected):")
    from collections import defaultdict
    by_topic = defaultdict(list)
    for r in results:
        by_topic[r["topic_expected"]].append(r)
    for t, sub in sorted(by_topic.items()):
        print(f"  {t[:25]:26}  n={len(sub):3}  hit={sum(1 for r in sub if r['hit'])/len(sub):.0%}  "
              f"recall={statistics.mean(r['recall'] for r in sub):.3f}")

    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\nConsultas SIN hit ({len(misses)}):")
        for r in misses[:15]:
            print(f"  {r['query_id']} [{r['difficulty']}]: {r['query'][:70]}")
        if len(misses) > 15:
            print(f"  ... y {len(misses) - 15} más")

    # Export JSONL
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        with args.export.open("w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        log.info(f"Resultados exportados a {args.export}")

    # Export Markdown
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        md = []
        md.append(f"# Reporte de evaluación RAG — k={args.k}\n")
        md.append(f"**Modelo de embedding:** `{EMBEDDING_MODEL}`\n")
        md.append(f"**Chunks indexados:** {len(chunks)}  ·  **Queries:** {len(results)}\n")
        md.append("\n## Métricas\n")
        md.append(f"| Métrica | Valor | Umbral | Estado |")
        md.append(f"|---|---:|---:|:---:|")
        md.append(f"| Hit rate @ k | {hit_rate:.2%} | {MIN_HIT:.2%} | {'✅' if hit_rate >= MIN_HIT else '❌'} |")
        md.append(f"| Recall promedio | {recall_m:.3f} | {MIN_RECALL:.3f} | {'✅' if recall_m >= MIN_RECALL else '❌'} |")
        md.append(f"| MRR | {mrr:.3f} | {MIN_MRR:.3f} | {'✅' if mrr >= MIN_MRR else '❌'} |")
        if citation_rate is not None:
            md.append(f"| Citation match | {citation_rate:.2%} | {MIN_CITATION:.2%} | {'✅' if citation_rate >= MIN_CITATION else '❌'} |")
        if misses:
            md.append(f"\n## Consultas sin hit ({len(misses)})\n")
            for r in misses[:20]:
                md.append(f"- `{r['query_id']}` [{r['difficulty']}] → {r['query']}")
        args.markdown.write_text("\n".join(md))
        log.info(f"Reporte markdown exportado a {args.markdown}")

    # Enforce thresholds
    failed = []
    if hit_rate < MIN_HIT:
        failed.append(f"Hit rate {hit_rate:.2%} < {MIN_HIT:.2%}")
    if recall_m < MIN_RECALL:
        failed.append(f"Recall {recall_m:.3f} < {MIN_RECALL:.3f}")
    if mrr < MIN_MRR:
        failed.append(f"MRR {mrr:.3f} < {MIN_MRR:.3f}")
    if citation_rate is not None and citation_rate < MIN_CITATION:
        failed.append(f"Citation {citation_rate:.2%} < {MIN_CITATION:.2%}")

    if failed:
        print("\n❌ Umbrales no superados:")
        for f in failed:
            print(f"   {f}")
        if args.strict:
            sys.exit(1)
        else:
            log.warning("Umbrales no superados pero --strict no activo; exit 0")

    print("\n✅ Evaluación OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
