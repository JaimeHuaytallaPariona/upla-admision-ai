"""Capa LLM intercambiable: Claude (prototipo) → Ollama (producción local)."""
from app.config import get_settings
from app.llm.base import LLMProvider

_instance: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _instance
    if _instance is not None:
        return _instance

    settings = get_settings()
    if settings.llm_provider == "claude":
        from app.llm.claude import ClaudeProvider
        _instance = ClaudeProvider()
    elif settings.llm_provider == "ollama":
        from app.llm.ollama import OllamaProvider
        _instance = OllamaProvider()
    else:
        raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")
    return _instance
