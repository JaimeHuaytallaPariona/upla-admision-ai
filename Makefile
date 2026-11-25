.PHONY: help up down logs api-shell web-shell db-shell rag-ingest rag-eval test lint build clean

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up:  ## Levanta todo el stack (postgres + api + web)
	docker compose up -d --build

down:  ## Baja el stack
	docker compose down

logs:  ## Sigue los logs de los servicios
	docker compose logs -f api web

api-shell:  ## Shell dentro del contenedor del API
	docker compose exec api bash

web-shell:  ## Shell dentro del contenedor del Web
	docker compose exec web sh

db-shell:  ## psql dentro de postgres
	docker compose exec postgres psql -U upla -d upla_admision

rag-ingest:  ## Re-ingesta el RAG manualmente (bootstrap es automático al arrancar)
	docker compose exec api python -c "from app.db import SessionLocal; from app.rag.store import bootstrap_index_if_empty; db=SessionLocal(); print(bootstrap_index_if_empty(db))"

rag-eval:  ## Corre el golden set contra el índice
	docker compose exec api python /rag-kb/scripts/evaluate.py --k 5 --store pgvector --provider local

test:  ## Corre los tests del backend
	docker compose exec api pytest -v

lint:  ## Lint del backend y frontend
	docker compose exec api python -m py_compile app/main.py
	docker compose exec web npm run lint

build:  ## Construye imágenes sin cache
	docker compose build --no-cache

clean:  ## Baja el stack y borra los volúmenes (destructivo)
	docker compose down -v

status:  ## Estado de los servicios
	docker compose ps
	@echo ""
	@curl -s http://localhost:8000/info 2>/dev/null | python3 -m json.tool || echo "API no responde todavía"
