# Arquitectura del Sistema

Este documento describe la arquitectura técnica del Sistema Multiagente para la Gestión Dinámica del Proceso de Admisión UPLA. Para el diseño detallado del RAG (base de conocimiento), ver [`Diseno_RAG_Carga_Inicial.docx`](./Diseno_RAG_Carga_Inicial.docx).

## 1. Vista de contenedores (C4 — nivel 2)

```
┌─────────────────┐     ┌──────────────────┐
│   Postulante    │     │   Personal       │
│   (web/mobile)  │     │   Oficina Admis. │
└────────┬────────┘     └──────────┬───────┘
         │                         │
   HTTPS │                         │ HTTPS
         ▼                         ▼
   ┌───────────────────────────────────────┐
   │       Next.js 14 (apps/web)           │
   │   - Landing, Chat, Panel admin        │
   └──────────────────┬────────────────────┘
                      │ fetch (rewrite)
                      ▼
   ┌───────────────────────────────────────┐
   │       FastAPI (apps/api)              │
   │   - Orquestador + agentes             │
   │   - Pipeline RAG                      │
   │   - APIs de admin y WhatsApp          │
   └────┬──────────────┬───────────┬───────┘
        │              │           │
        ▼              ▼           ▼
   ┌────────┐   ┌────────────┐  ┌──────────────┐
   │Postgres│   │ Anthropic  │  │  bge-m3      │
   │pgvector│   │  / Ollama  │  │  (en API pod)│
   └────────┘   └────────────┘  └──────────────┘
```

## 2. Flujo de un turno conversacional

```
Mensaje del postulante
        │
        ▼
POST /api/v1/chat ───► Cargar sesión (o crear) ───► Persistir mensaje
        │
        ▼
¿Hay flujo de inscripción en curso?
    ├── Sí ──► InscriptionAgent continúa
    │
    └── No ──► ¿Hay awaiting='dni'?
               ├── Sí ──► ResultsAgent continúa
               │
               └── No ──► Clasificar intención (heurística + LLM fallback)
                           │
                           ▼
                        Routing a agente especializado:
                          greeting / rag / exam / inscription /
                          results / matricula / handoff
                           │
                           ▼
                        Agente ejecuta:
                          - (opcional) retrieve chunks de pgvector
                          - construir prompt
                          - invocar LLM (claude / ollama)
                           │
                           ▼
                        Resultado + citations + confidence + state_update
                           │
                           ▼
                        Persistir respuesta + actualizar fase/intent
                           │
                           ▼
                        ChatResponse (JSON) → frontend
```

## 3. Modelo de datos

```
sessions                     messages
─────────                    ────────
id (uuid)        ◄──────────── session_id
channel                       id
identity_level                role (user|assistant|system)
dni                           content
postulante_data               agent
current_phase                 citations (JSON)
current_intent                confidence
state (JSON)                  created_at
created_at
updated_at                    observations
                              ────────────
inscripciones                 id
─────────────                 session_id
id                            query
session_id                    reason (low_conf|user_req|out_of_scope)
codigo_inscripcion            status (pending|in_review|resolved)
dni, nombres, apellidos       assigned_to, resolution
email, telefono               created_at, resolved_at
modalidad, carrera, canal
estado                        kb_chunks
created_at                    ─────────
                              id (string)
                              text
                              embedding vector(1024)
                              metadata (JSONB)
                              content_hash
                              indexed_at
```

## 4. Decisiones arquitectónicas

### 4.1 Por qué máquina de estados en lugar de LangGraph

LangGraph aporta orquestación declarativa pero añade ~100 MB de dependencias y una capa de abstracción que complica debugging. Para un prototipo con 7 agentes, una máquina de estados en Python puro es más auditable y mantenible — se lee de arriba hacia abajo en `orchestrator.py`.

### 4.2 Por qué embeddings locales

- Zero dependencia externa en producción.
- bge-m3 es multilingüe y específicamente fuerte en español.
- 1024d encaja cómodamente en pgvector con HNSW.
- Alternativa (OpenAI text-embedding-3-small) queda documentada en `rag-kb/README.md`.

### 4.3 Por qué pgvector y no Qdrant

- La UPLA probablemente ya opera PostgreSQL; agregar `CREATE EXTENSION vector` es un cambio menor.
- 117 chunks iniciales y proyección de ~2000 no justifican un vector-store dedicado.
- JSONB nativo para los filtros categóricos sin ORM adicional.
- Migración a Qdrant queda abierta si la escala lo exige (>500k chunks).

### 4.4 Por qué dos niveles de identidad

- **Anónimo** — el 80% de consultas (información general) no requiere autenticación; obligar reduce conversión.
- **Autenticado** (DNI validado) — operaciones que tocan datos del postulante (resultados, estado de inscripción).
- Alinea con Ley N.° 29733: minimización de datos recolectados.

### 4.5 Por qué citación obligatoria en el prompt

- Blindaje contra alucinación.
- Trazabilidad para auditoría (SGC — Fase 3 pide verificabilidad).
- La Oficina de Admisión puede defender cada respuesta del sistema con el artículo del Reglamento.

## 5. Seguridad y privacidad

- Secretos (`ANTHROPIC_API_KEY`, `JWT_SECRET`) viven solo en `.env`, nunca en el repo.
- CORS limitado a `localhost:3000` y `web:3000` en dev; configurable en prod.
- DNI del postulante se almacena hasheado en el logging (pendiente, v0.3).
- Alineación Ley 29733:
  - Minimización — solo se pide el dato necesario para la operación en curso.
  - Finalidad — cada captura va acompañada de propósito explícito.
  - Derechos ARCO — el postulante puede pedir eliminación vía Oficina de Admisión.

## 6. Observabilidad

- `/api/v1/info` expone versión, LLM activo, conteo de chunks.
- Panel `/panel` consulta métricas cada 10s.
- Cada mensaje del asistente persiste `confidence`, `agent` y `citations` para análisis.
- Observaciones (consultas con baja confianza, derivaciones explícitas, fuera de ámbito) van a una bandeja consultable por la Oficina.

## 7. Despliegue

El prototipo corre en Docker Compose. Para producción UPLA:

| Servicio | Opción recomendada |
|---|---|
| API | Kubernetes o VM con systemd + uvicorn workers |
| Web | Vercel, Netlify o mismo K8s con Next.js standalone |
| Postgres | Managed (RDS, Azure, DO) o on-prem UPLA con backup diario |
| LLM | Ollama self-hosted en servidor GPU UPLA (reduce costo y mantiene datos dentro) |
| Monitoring | Prometheus + Grafana o Datadog |

## 8. Referencias

- [Next.js App Router](https://nextjs.org/docs/app)
- [FastAPI](https://fastapi.tiangolo.com/)
- [pgvector](https://github.com/pgvector/pgvector)
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Ollama](https://ollama.ai/)
