# Delta v0.2 — Eje 1: Grounding institucional completo

**Fecha:** 2026-11-26
**Alcance:** incorporar al RAG el ecosistema SGC completo de la Oficina de Admisión
(Fichas de Caracterización, Indicadores de Desempeño, Matriz AMFE de Riesgos) y
una línea de evaluación continua que impida que un commit degrade silenciosamente
la calidad de recuperación.

---

## Entregables

### 1 — Fichas SGC como chunks indexables  (`apps/rag-kb/data/fichas_sgc.jsonl`)

**104 chunks** derivados de las 14 fichas SGC-FC-PADM v02 (10/11/2026):

| Tipo de proceso | Procesos | Chunks |
|---|---:|---:|
| Estratégico | 4 (E01-01..04) | 30 |
| Misional | 5 (M01-01..05) | 36 |
| De apoyo | 5 (A01-01..05) | 38 |

Cada ficha se descompone en 7-8 chunks temáticos: `RESUMEN`, `INSUMOS`,
`ACTIVIDADES`, `PRODUCTOS`, `CONTROLES`, `RIESGOS`, `RECURSOS`, `INDICADORES`.
Los chunks de riesgos marcan `sensitivity: authenticated_only`; el resto son
`public` (información institucional abierta).

### 2 — Indicadores de desempeño  (`apps/rag-kb/data/indicadores_sgc.jsonl`)

**36 chunks** derivados de las fichas SGC-IND-PADM v02. Cada chunk cubre el
indicador completo: nombre, tipo (de proceso / de producto), método de cálculo,
meta, frecuencia, responsable, fuente de datos, oportunidad de la medida,
justificación, limitaciones y estado de la línea de base.

### 3 — Matriz AMFE de riesgos  (`apps/rag-kb/data/riesgos_amfe.jsonl`)

**18 chunks** derivados de SGC-GDR-PADM-01 v02. Cada chunk cubre el riesgo
completo: actividad asociada, modo de fallo, efecto, causa, controles actuales,
valoración G×O×D, NR, clasificación, acciones de mitigación, responsable,
fecha reprogramada y revaloración prevista. **Sensibilidad:
`authenticated_only`** — son información operativa interna.

### 4 — Golden set expandido  (`apps/rag-kb/data/golden_sgc.jsonl`)

**72 consultas adicionales** (Q031..Q102), que llevan el total de 30 → 102
queries. Cobertura:

| Tema | Queries |
|---|---:|
| proceso_sgc | 24 |
| indicador | 24 |
| riesgo | 16 |
| responsable | 4 |
| actividad | 4 |
| Cruzadas Reglamento+SGC | 10 |

Dificultad: 19 easy, 38 medium, 15 hard. Sensibilidad: 56 public, 16
authenticated_only.

### 5 — Schema actualizado  (`apps/rag-kb/schema/chunks_schema.json`)

Nuevos `source_type` admitidos: `ficha_proceso`, `indicador_sgc`, `riesgo_amfe`.
Nuevos `topic`: `proceso_sgc`, `indicador`, `riesgo`, `responsable`,
`actividad`, `sgc_general`. Backwards-compatible con los chunks v0.1.

### 6 — Pipeline de evaluación continua  (`.github/workflows/rag-eval.yml` + `apps/rag-kb/scripts/evaluate_ci.py`)

Workflow GitHub Actions que se dispara en cada push/PR a `apps/rag-kb/**`:

1. Valida los chunks contra el schema JSON.
2. Carga todos los JSONL en memoria.
3. Embedding con `fastembed` (mismo modelo que la app: `BAAI/bge-small-en-v1.5`).
4. Ejecuta las 102 queries golden y calcula Hit rate, Recall, MRR, Citation match.
5. **Falla el PR** si alguna métrica cae bajo los umbrales.
6. Publica un reporte markdown como comentario del PR.
7. Guarda los resultados como artefacto 30 días.

**Umbrales iniciales** (env-configurable en el workflow):

| Métrica | Umbral | Nota |
|---|---:|---|
| Hit rate @ 5 | 85% | Baseline TF-IDF ≈ 76%, fastembed debería superarlo |
| Recall promedio | 0.70 | |
| MRR | 0.65 | |
| Citation match top-1 | 70% | Solo aplica a queries con `citation_required` (30 del Reglamento) |

> La evaluación es **in-memory** (no levanta Postgres). Tiempo estimado por
> ejecución: ~30-45 s en un runner estándar de GitHub Actions. El cache de
> fastembed queda guardado entre ejecuciones.

---

## Totales del delta

| Categoría | Archivos | Chunks nuevos |
|---|---:|---:|
| Fichas SGC | 1 | 104 |
| Indicadores | 1 | 36 |
| Riesgos AMFE | 1 | 18 |
| Golden set | 1 | 72 queries |
| Schema (actualizado) | 1 | — |
| Scripts | 1 | — |
| Workflow CI | 1 | — |
| **Total** | **7** | **158 chunks + 72 queries** |

Crecimiento del RAG: **87 chunks v0.1 → 245 chunks v0.2** (≈ 2.8×).
Golden set: **30 → 102 queries** (3.4×).

---

## Verificación local previa al commit

```bash
# Desde la raíz del repo, después de aplicar el delta:
cd apps/rag-kb
pip install fastembed numpy jsonschema

# Validar schema
python -c "
import json, jsonschema
from pathlib import Path
schema = json.loads(Path('schema/chunks_schema.json').read_text())
v = jsonschema.Draft7Validator(schema)
errs = 0
for p in sorted(Path('data').glob('*.jsonl')):
    if 'golden' in p.name: continue
    for i, l in enumerate(p.open(), 1):
        if not l.strip(): continue
        c = json.loads(l)
        for e in v.iter_errors(c):
            errs += 1
            print(f'{p.name}:{i} — {e.message}')
print(f'Errores: {errs}')
"

# Ejecutar evaluador (requiere descargar el modelo la primera vez, ~130MB)
python scripts/evaluate_ci.py --k 5 --strict
```
