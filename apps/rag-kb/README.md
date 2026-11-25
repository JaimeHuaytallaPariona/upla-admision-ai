# Base de Conocimiento RAG — Sistema Conversacional de Admisión UPLA

Carga inicial del índice RAG para el asistente conversacional del proceso de admisión.
Versión 1.0 · 25 de noviembre de 2026.

## Contenido

```
rag-kb-v1/
├── README.md                          ← este archivo
├── schema/
│   └── chunks_schema.json             Esquema JSON-Schema de los chunks
├── data/
│   ├── reglamento_chunks.jsonl        56 chunks del Reglamento 311-2025-CU-UPLA
│   ├── modalidades.jsonl              13 modalidades estructuradas
│   ├── canales.jsonl                  5 canales con ponderación de examen
│   └── golden_eval.jsonl              30 consultas golden con respuesta esperada
├── scripts/
│   ├── ingest.py                      Pipeline de ingesta al vector store
│   └── evaluate.py                    Evaluación del recall del índice
└── docs/
    └── Diseno_RAG_Carga_Inicial.docx  Documento de diseño (18 páginas)
```

## Fuentes

- **Reglamento General de Admisión de Pregrado UPLA** — Resolución de Consejo Universitario N.° 311-2025-CU-UPLA, aprobada el 28/02/2025, vigencia desde 03/03/2025. 16 páginas, 50 artículos + 6 disposiciones complementarias.
- **Fichas SGC v02** — próximamente (14 fichas de caracterización, 36 indicadores, 18 riesgos AMFE).

## Puesta en marcha

### Entorno

```bash
pip install openai psycopg2-binary qdrant-client sentence-transformers
export OPENAI_API_KEY="sk-…"
export PGVECTOR_CONN="postgresql://user:pass@localhost:5432/upla_rag"
```

### Dry-run (validar los JSONL)

```bash
python scripts/ingest.py --all --dry-run
```

### Ingesta real

```bash
python scripts/ingest.py --all --store pgvector --provider openai
```

### Evaluación

```bash
python scripts/evaluate.py --k 5 --store pgvector
```

Umbrales mínimos aceptados para pasar a piloto:

| Métrica | Umbral |
|---|---|
| Hit rate (@ k=5) | ≥ 95 % |
| Recall promedio | ≥ 0.85 |
| MRR | ≥ 0.75 |
| Citación correcta en top-1 | ≥ 80 % |

## Política de versionado

El índice se versiona por `version` en cada chunk. Un cambio en el Reglamento
(nueva resolución) genera un ciclo completo de reindexación: todos los chunks
afectados suben `version` y vuelven a embedding. El sistema de producción
mantiene los índices anterior y nuevo en paralelo durante 72 horas para
compatibilidad.

Nunca se mezclan chunks de dos resoluciones distintas en el mismo índice
sin estrategia de deprecación explícita.

## Gobernanza

| Rol | Responsabilidad |
|---|---|
| Jefe de Oficina de Admisión | Aprobación del contenido (dueño del proceso A01-04) |
| Equipo del proyecto | Mantenimiento técnico del índice y del pipeline |
| Oficina de Gestión de la Calidad | Control documental de versiones |
| TI UPLA | Operación del vector store en producción |

## Ciclo de vida

1. **Edición** — se edita el chunk en el JSONL correspondiente (nunca en el vector store).
2. **Commit** — cambio en Git con mensaje referido al artículo y la resolución fuente.
3. **Re-embedding** — `python scripts/ingest.py --source <archivo>` detecta el cambio por `content_hash` y re-indexa solo los chunks modificados.
4. **Evaluación** — `python scripts/evaluate.py` verifica que no se degradan las métricas.
5. **Aprobación** — pull request revisado por el dueño del proceso antes de merge a `main`.
6. **Despliegue** — pipeline CI/CD aplica a producción.
