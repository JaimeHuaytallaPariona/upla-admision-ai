# Changelog

Todos los cambios notables a este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] — 2026-11-25

### Añadido

**Backend (FastAPI)**
- Orquestador multiagente con máquina de estados y 7 agentes especializados:
  `greeting`, `rag`, `exam`, `inscription`, `results`, `matricula`, `handoff`.
- Router de intención híbrido (heurístico + LLM) sobre 12 intents.
- Capa LLM intercambiable: `claude` (Anthropic API) o `ollama` (local).
- Pipeline RAG con bge-m3 local (1024 dims) y pgvector.
- Bootstrap automático del índice al arrancar el API.
- Endpoints del panel administrativo: metrics, observations, inscripciones, sessions.
- Webhook de WhatsApp (stub con verificación Meta).
- Modelo de identidad de dos niveles (anonymous / authenticated).
- Persistencia completa de sesiones, mensajes, observaciones e inscripciones.
- Tests unitarios del router de intención y de los catálogos mock.

**Frontend (Next.js 14)**
- Landing con el valor del asistente y acceso directo al chat.
- Interfaz de chat con indicador de fase del embudo, quick-replies, citas inline y badges de confianza/agente.
- Panel administrativo con KPIs en vivo (refresca cada 10s) y tres tablas: observaciones, inscripciones, sesiones.

**RAG**
- 117 chunks oficiales: 69 del Reglamento 311-2025-CU-UPLA + 13 modalidades + 5 canales + 30 consultas golden de evaluación.
- Pipeline de ingesta `ingest.py` y evaluador `evaluate.py`.
- Documento de diseño DOCX de 18 páginas.

**Infraestructura**
- Docker Compose con pgvector/pg16, api y web.
- Dockerfiles multi-stage para api y web.
- Makefile con atajos (`up`, `down`, `logs`, `test`, `rag-eval`, `clean`, etc.).
- GitHub Actions: CI (lint + test) y build de imágenes.
- Templates de issue y pull request.
- Variables de entorno documentadas en `.env.example`.
