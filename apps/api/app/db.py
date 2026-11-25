"""Conexión a PostgreSQL con pgvector."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# NullPool porque en contenedores con reinicios frecuentes evita conexiones huérfanas.
engine = create_engine(settings.database_url, poolclass=NullPool, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa esquema + extensión pgvector. Idempotente."""
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    from app.models.db_models import Base as ModelsBase
    ModelsBase.metadata.create_all(engine)
