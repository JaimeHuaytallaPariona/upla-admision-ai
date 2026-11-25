<div align="center">

# UPLA Admisión AI

### Sistema multiagente para la gestión dinámica del proceso de admisión
### en la Universidad Peruana Los Andes

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009485.svg)
![pgvector](https://img.shields.io/badge/pgvector-0.3-336791.svg)
![Status](https://img.shields.io/badge/status-prototipo_funcional-orange.svg)

**Asistente conversacional que acompaña al postulante durante todo el embudo de admisión**  
Atención → Inscripción → Examen → Resultados → Matrícula

</div>

---

## Tabla de contenidos

1. [¿Qué es esto?](#qué-es-esto)
2. [Arquitectura](#arquitectura)
3. [Puesta en marcha](#puesta-en-marcha-5-minutos)
4. [Estructura del repositorio](#estructura-del-repositorio)
5. [Flujos funcionales](#flujos-funcionales-del-prototipo)
6. [RAG — base de conocimiento](#rag--base-de-conocimiento)
7. [API](#api)
8. [Demos reproducibles](#demos-reproducibles)
9. [Roadmap](#roadmap)
10. [Licencia y créditos](#licencia-y-créditos)

---

## ¿Qué es esto?

Prototipo funcional de un sistema conversacional multiagente, diseñado como solución al problema de gestión dinámica de los procesos de admisión en la UPLA. El sistema cubre el embudo completo de admisión con cinco agentes especializados coordinados por un orquestador, apoyado en una base de conocimiento RAG construida sobre el **Reglamento General de Admisión (Res. 311-2025-CU-UPLA)**.

**Principios de diseño:**

- **Human-in-the-loop** — el asistente informa y gestiona, pero jamás decide admisión; cuando la confianza baja o el caso lo amerita, deriva a un asesor humano.
- **Grounding verificable** — toda respuesta informativa se cita contra el Reglamento; el asistente no inventa.
- **Identidad de dos niveles** — modo anónimo (información pública) y modo autenticado (operaciones con DNI).
- **Observabilidad desde el día uno** — panel administrativo con métricas en tiempo real, bandeja de observaciones y trazabilidad por sesión.
- **Portable** — corre con `docker compose up` en cualquier máquina con Docker.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CANALES DE ENTRADA                              │
│   Web Chat (Next.js 14)        WhatsApp Webhook (stub, listo Meta)      │
└──────────────────┬──────────────────────────────┬───────────────────────┘
                   │                              │
                   └──────────────┬───────────────┘
                                  │
                   ┌──────────────▼──────────────┐
                   │   API Gateway (FastAPI)     │
                   │   POST /api/v1/chat         │
                   └──────────────┬──────────────┘
                                  │
                   ┌──────────────▼──────────────┐
                   │    ORQUESTADOR MULTIAGENTE  │
                   │  (Router de intención +     │
                   │   máquina de estados)       │
                   └─┬────┬────┬────┬────┬────┬──┘
                     │    │    │    │    │    │
             ┌───────┘    │    │    │    │    └────────┐
             ▼            ▼    ▼    ▼    ▼             ▼
       ┌──────────┐ ┌──────┐┌────┐┌───┐┌─────┐  ┌──────────┐
       │ Greeting │ │ RAG  ││Exam││Insc││Resul│  │ Handoff  │
       │  Agent   │ │Agent ││Agnt││Agnt││Agnt │  │  Agent   │
       └──────────┘ └──┬───┘└──┬─┘└─┬──┘└──┬──┘  └────┬─────┘
                       │       │   │       │          │
                       │       │   │       │          └──► Bandeja de
                       │       │   │       │                observaciones
                       │       │   │       └──► mock/resultados.py
                       │       │   └─► mock/catalogo_carreras.py
                       │       └─► mock/cronograma.py
                       │
              ┌────────▼────────┐
              │  Retriever RAG  │
              │  (semántico +   │
              │   filtros)      │
              └────────┬────────┘
                       │
              ┌────────▼────────┐          ┌────────────────────┐
              │  pgvector (PG)  │◄─────────┤  Embedder          │
              │  117 chunks     │          │  BAAI/bge-m3 local │
              │  oficiales      │          └────────────────────┘
              └─────────────────┘
                       ▲
                       │ embeddings
              ┌────────┴────────┐
              │   LLM Provider  │
              │ (Claude / Ollama)│
              └─────────────────┘
```

### Stack tecnológico

| Capa | Tecnología | Por qué |
|---|---|---|
| **Frontend** | Next.js 14 + TypeScript + Tailwind | SSR, rutas limpias, bundle liviano |
| **Backend** | FastAPI + SQLAlchemy 2.0 | Async-first, docs OpenAPI automáticas |
| **LLM** | Claude Haiku 4.5 (demo) / Ollama 3.1 (prod) | Adaptable vía `LLM_PROVIDER` |
| **Embeddings** | BAAI/bge-m3 local (1024d) | Sin dependencia externa, multilingüe |
| **Vector store** | PostgreSQL 16 + pgvector | Mismo motor que operan en la UPLA |
| **Orquestación** | Máquina de estados Python | Cero magia; auditable y debuggeable |
| **Despliegue** | Docker Compose | Portabilidad total |
| **CI** | GitHub Actions | Lint + test en cada PR |

---

## Puesta en marcha (5 minutos)

### Requisitos previos

- Docker Desktop 24+ con Docker Compose v2
- (Opcional) API key de Anthropic para usar Claude. Alternativa: `ollama` corriendo localmente.

### Pasos

```bash
# 1. Clonar el repo
git clone https://github.com/<tu-usuario>/upla-admision-ai.git
cd upla-admision-ai

# 2. Configurar variables
cp .env.example .env
# Edita .env y agrega tu ANTHROPIC_API_KEY (o cambia LLM_PROVIDER=ollama)

# 3. Levantar todo el stack
make up
# (equivalente a: docker compose up -d --build)

# 4. Esperar ~90 segundos a que:
#    - Postgres inicialice
#    - API descargue el modelo de embeddings (1.1 GB, primera vez)
#    - API bootstrapee los 117 chunks al índice
#    - Web compile y arranque

# 5. Verificar
make status

# 6. Abrir en navegador
#    → http://localhost:3000       Página de inicio
#    → http://localhost:3000/chat  Asistente conversacional
#    → http://localhost:3000/panel Panel administrativo
#    → http://localhost:8000/docs  Swagger de la API
```

### Comandos útiles del Makefile

```bash
make help         # Lista todos los comandos
make logs         # Sigue logs de API y Web
make db-shell     # Abre psql dentro de Postgres
make test         # Corre los tests del backend
make rag-eval     # Evalúa el RAG contra el golden set (30 consultas)
make clean        # Baja todo y borra volúmenes (destructivo)
```

---

## Estructura del repositorio

```
upla-admision-ai/
├── apps/
│   ├── api/                              Backend FastAPI
│   │   ├── app/
│   │   │   ├── agents/                   Orquestador + 7 agentes especializados
│   │   │   │   ├── orchestrator.py       Router principal
│   │   │   │   ├── intent_router.py      Clasificación heurística + LLM fallback
│   │   │   │   ├── rag_agent.py          Respuestas informativas con citación
│   │   │   │   ├── exam_agent.py         Canales, asignaturas, ponderación
│   │   │   │   ├── inscription_agent.py  Captura de datos paso a paso
│   │   │   │   ├── results_agent.py      Consulta por DNI (mock)
│   │   │   │   ├── matricula_agent.py    Derivación post-ingreso
│   │   │   │   ├── handoff_agent.py      Derivación humana con registro
│   │   │   │   ├── greeting_agent.py     Saludo y despedida
│   │   │   │   └── prompts.py            System prompts versionados
│   │   │   ├── api/                      Routers HTTP
│   │   │   │   ├── chat.py               POST /chat — entry-point
│   │   │   │   ├── sessions.py           GET /sessions/{id}
│   │   │   │   ├── admin.py              Panel de métricas y observaciones
│   │   │   │   ├── whatsapp.py           Webhook Meta (stub)
│   │   │   │   └── health.py             /health y /info
│   │   │   ├── rag/
│   │   │   │   ├── embedder.py           bge-m3 local
│   │   │   │   ├── retriever.py          Recuperación híbrida pgvector
│   │   │   │   └── store.py              Bootstrap automático del índice
│   │   │   ├── llm/
│   │   │   │   ├── claude.py             Provider Anthropic
│   │   │   │   └── ollama.py             Provider local
│   │   │   ├── models/
│   │   │   │   ├── db_models.py          Session, Message, KBChunk, Observation, Inscripcion
│   │   │   │   └── schemas.py            Pydantic request/response
│   │   │   ├── mock/                     Catálogos y datos sintéticos
│   │   │   ├── config.py                 Settings vía pydantic-settings
│   │   │   ├── db.py                     SQLAlchemy engine
│   │   │   └── main.py                   FastAPI app
│   │   ├── tests/                        pytest
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── web/                              Frontend Next.js 14
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── page.tsx              Landing
│   │   │   │   ├── chat/page.tsx         Interfaz conversacional
│   │   │   │   └── panel/page.tsx        Panel admin con tabs
│   │   │   ├── components/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── Message.tsx
│   │   │   │   └── PhaseIndicator.tsx
│   │   │   └── lib/
│   │   │       ├── api.ts                Cliente HTTP
│   │   │       └── types.ts
│   │   ├── package.json
│   │   └── Dockerfile
│   └── rag-kb/                           Base de conocimiento (paquete independiente)
│       ├── data/                         4 archivos JSONL
│       ├── schema/
│       ├── scripts/
│       └── docs/Diseno_RAG_Carga_Inicial.docx
├── docs/                                 Documentación del proyecto
│   ├── architecture.md
│   └── Diseno_RAG_Carga_Inicial.docx
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                        Lint + test en PR
│   │   └── docker.yml                    Build de imágenes
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── scripts/                              Scripts auxiliares
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
├── LICENSE                               MIT
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md                             ← estás aquí
```

---

## Flujos funcionales del prototipo

### 1. Atención informativa (RAG)
Pregunta: *"¿Qué documentos necesito para postular?"* → `rag_agent` → retrieve top-5 chunks → genera respuesta citando Art. 10° del Reglamento.

### 2. Inscripción paso a paso
Disparador: *"Quiero inscribirme"* → `inscription_agent` entra en modo captura y pide secuencialmente: DNI → nombres → apellidos → correo → celular → modalidad → carrera → confirmación. Al final genera código `UPLA-2026-XXXXXX` y persiste en la tabla `inscripciones`.

### 3. Examen — composición por canal
Pregunta: *"¿Qué materias entran para Medicina?"* → `exam_agent` infiere canal V → recupera la ponderación → responde con tabla + cronograma.

### 4. Resultados autenticados
Pregunta: *"¿Ingresé?"* → `results_agent` solicita DNI → valida contra `mock/resultados.py` → responde con puntaje y puesto. DNIs de demo: **71234567**, **72345678**, **73456789**, **74567890**, **75678901**.

### 5. Matrícula (fuera de ámbito, deriva)
Pregunta: *"¿Cómo me matriculo?"* → `matricula_agent` informa y deriva a Servicios Académicos.

### 6. Derivación humana
Disparador: *"Quiero hablar con una persona"* → `handoff_agent` registra observación en bandeja + entrega contactos.

---

## RAG — base de conocimiento

Vive en `apps/rag-kb/` como paquete independiente que el backend consume en arranque.

- **117 chunks oficiales**: 69 del Reglamento (definiciones, 56 artículos, 5 ponderaciones de canal, disposiciones complementarias) + 13 modalidades + 5 canales + 30 consultas golden de evaluación.
- **Taxonomías cerradas** para filtrado híbrido: 18 temas, 14 modalidades, 6 canales, 3 niveles de sensibilidad.
- **Embeddings**: `BAAI/bge-m3` (1024d, local, multilingüe).
- **Evaluación**: `make rag-eval` ejecuta las 30 consultas golden y reporta Hit rate, Recall, MRR y coincidencia de citación. Umbrales para piloto: Hit rate ≥95%, Recall ≥0.85, MRR ≥0.75, Citación ≥80%.
- **Documento de diseño completo**: `docs/Diseno_RAG_Carga_Inicial.docx` (18 páginas).

Detalles en [`apps/rag-kb/README.md`](apps/rag-kb/README.md).

---

## API

OpenAPI auto-generado en `http://localhost:8000/docs`. Endpoints principales:

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/api/v1/chat` | Mensaje al asistente; retorna respuesta + agent + citas |
| GET | `/api/v1/sessions/{id}` | Metadata de una sesión |
| GET | `/api/v1/sessions/{id}/messages` | Historial completo |
| GET | `/api/v1/admin/metrics` | KPIs del panel |
| GET | `/api/v1/admin/observations` | Bandeja de derivaciones pendientes |
| GET | `/api/v1/admin/inscripciones` | Pre-inscripciones capturadas |
| GET | `/api/v1/admin/sessions` | Listado reciente |
| GET | `/api/v1/whatsapp/webhook` | Verificación Meta (stub) |
| POST | `/api/v1/whatsapp/webhook` | Recepción de mensajes WhatsApp (stub) |
| GET | `/api/v1/health` | Healthcheck |
| GET | `/api/v1/info` | Versión, modelo LLM, # chunks indexados |

---

## Demos reproducibles

Secuencia sugerida para una demo ejecutiva de 10 minutos:

1. **Landing** (http://localhost:3000) — mostrar el valor en 15 segundos.
2. **Iniciar chat** → *"¿Cuáles son las modalidades?"* → observar las citas al Reglamento.
3. *"¿Qué materias entran para Medicina?"* → mostrar la detección de canal.
4. *"Quiero inscribirme"* → completar el flujo paso a paso.
5. *"¿Ingresé? Mi DNI es 73456789"* → resultado positivo con puntaje.
6. *"Necesito hablar con una persona"* → derivación registrada.
7. **Panel admin** (`/panel`) — mostrar KPIs, observaciones y la pre-inscripción generada.

---

## Roadmap

- [x] **v0.1 — Prototipo funcional end-to-end** (actual)
- [ ] v0.2 — SSO institucional (OpenID Connect) + perfil persistente del postulante
- [ ] v0.3 — Integración WhatsApp Business Platform real (Meta)
- [ ] v0.4 — Streaming de respuestas (SSE)
- [ ] v0.5 — Fichas SGC completas en el RAG (14 procesos, 36 indicadores, 18 riesgos AMFE)
- [ ] v0.6 — Pipeline de evaluación continua en CI con regresión
- [ ] v1.0 — **Piloto en UPLA** con TI, Admisión y SGC

---

## Licencia y créditos

**Licencia MIT** — libre para uso académico e institucional, con atribución.

**Autor**: Msc. Jaime Antonio Huaytalla Pariona  
**Institución**: Universidad Peruana Los Andes · Facultad de Ingeniería  
**Marco**: tesis de maestría en Inteligencia Artificial, UNI

**Fuentes normativas**:
- Resolución N.° 311-2025-CU-UPLA — Reglamento General de Admisión de Pregrado UPLA
- Norma Técnica N.° 002-2025-PCM-SGP — Gestión por procesos en la administración pública
- Ley N.° 29733 — Protección de Datos Personales

---

<div align="center">

**Huancayo · Perú · 2026**

</div>
