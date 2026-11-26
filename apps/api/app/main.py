"""Punto de entrada del backend FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import admin, chat, health, sessions, whatsapp
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.rag.store import bootstrap_index_if_empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Iniciando {settings.app_name} v{__version__} (env={settings.app_env})")
    init_db()
    db = SessionLocal()
    try:
        bootstrap_index_if_empty(db)
    except Exception as e:
        log.warning(f"Bootstrap del indice fallo (se puede ejecutar despues): {e}")
    finally:
        db.close()
    # Pre-cargar el embedder para que la primera consulta no pague el costo
    try:
        from app.rag.embedder import embed
        _ = embed("warmup")
        log.info("Embedder precargado y listo para servir.")
    except Exception as e:
        log.warning(f"Pre-carga del embedder fallo: {e}")
    yield
    log.info("Apagando backend.")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Backend conversacional multiagente para el proceso de admision UPLA.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_prefix
app.include_router(health.router, prefix=prefix)
app.include_router(chat.router, prefix=prefix)
app.include_router(sessions.router, prefix=prefix)
app.include_router(admin.router, prefix=prefix)
app.include_router(whatsapp.router, prefix=prefix)


@app.get("/")
def root():
    return {"service": settings.app_name, "version": __version__, "docs": "/docs"}
