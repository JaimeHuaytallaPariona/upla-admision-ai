"""Contrato común para proveedores LLM."""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interfaz mínima que todo proveedor LLM debe satisfacer."""

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """Generar respuesta dada una conversación. Retorna texto plano."""
        ...

    @abstractmethod
    def classify_intent(self, user_message: str, intents: list[str]) -> tuple[str, float]:
        """Clasifica la intención del mensaje. Retorna (intent, confidence)."""
        ...
