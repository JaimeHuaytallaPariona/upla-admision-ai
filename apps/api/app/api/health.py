"""Endpoint de salud y metadata del servicio."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.config import get_settings
from app.db import get_db
from app.rag.store import count_chunks

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@router.get("/info")
def info(db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        chunks = count_chunks(db)
        db_ok = True
    except Exception:
        chunks = 0
        db_ok = False
    return {
        "app": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.claude_model if settings.llm_provider == "claude" else settings.ollama_model,
        "embedding_model": settings.embedding_model,
        "db_ok": db_ok,
        "kb_chunks": chunks,
    }
