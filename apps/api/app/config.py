"""Configuración centralizada del backend. Todas las variables se leen de entorno."""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "UPLA Admisión AI"
    app_env: Literal["dev", "staging", "prod"] = "dev"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://web:3000"]

    # Database (pgvector)
    database_url: str = "postgresql://upla:upla@postgres:5432/upla_admision"

    # LLM provider
    llm_provider: Literal["claude", "ollama"] = "claude"
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-4-5"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"

    # Embeddings (local por defecto, cero dependencia externa)
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024

    # RAG
    rag_top_k: int = 5
    rag_confidence_threshold: float = 0.65

    # Identidad
    sso_enabled: bool = False
    jwt_secret: str = "change-me-in-production"

    # WhatsApp (stub)
    whatsapp_enabled: bool = False
    whatsapp_verify_token: str = "upla-admision-verify"


@lru_cache
def get_settings() -> Settings:
    return Settings()
