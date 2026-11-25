"""Proveedor Claude (Anthropic API)."""
import json
import logging
from typing import Any

from anthropic import Anthropic

from app.config import get_settings
from app.llm.base import LLMProvider

log = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            log.warning("ANTHROPIC_API_KEY no configurada; las llamadas a Claude fallarán.")
        self.client = Anthropic(api_key=settings.anthropic_api_key or "sk-not-configured")
        self.model = settings.claude_model

    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            )
            parts = []
            for block in resp.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
            return "".join(parts).strip()
        except Exception as e:
            log.exception("Fallo al invocar Claude")
            return (
                "Lo siento, estoy teniendo un problema técnico para procesar tu consulta. "
                "Te derivaré a un asesor de la Oficina de Admisión. (Error: {})".format(str(e)[:80])
            )

    def classify_intent(self, user_message: str, intents: list[str]) -> tuple[str, float]:
        system = (
            "Eres un clasificador de intenciones del asistente de admisión UPLA. "
            "Dada la consulta de un postulante, selecciona UNA intención de la lista. "
            "Responde SOLO con JSON válido: {\"intent\": \"...\", \"confidence\": 0.0-1.0}. "
            f"Intenciones válidas: {', '.join(intents)}. "
            "Si ninguna aplica, usa \"info_general\" con confidence baja."
        )
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.0,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
            # Limpieza ante posibles bloques markdown
            if text.startswith("```"):
                text = text.split("```")[1].replace("json", "", 1).strip()
            data = json.loads(text)
            intent = data.get("intent", "info_general")
            if intent not in intents:
                intent = "info_general"
            conf = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            return intent, conf
        except Exception as e:
            log.warning(f"Fallback en clasificación de intención: {e}")
            return "info_general", 0.3
