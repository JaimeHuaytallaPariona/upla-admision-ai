"""Proveedor Ollama (modelo local). Alternativa sin dependencias externas."""
import json
import logging
import httpx

from app.config import get_settings
from app.llm.base import LLMProvider

log = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        chat_msgs = [{"role": "system", "content": system}] + messages
        try:
            r = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": chat_msgs,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=180.0,
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except Exception as e:
            log.exception("Fallo al invocar Ollama")
            return f"Lo siento, estoy teniendo un problema tecnico. (Error: {str(e)[:80]})"

    def classify_intent(self, user_message: str, intents: list[str]) -> tuple[str, float]:
        prompt = (
            "Clasifica la intencion de un postulante universitario UPLA.\n\n"
            "REGLAS IMPORTANTES para distinguir preguntas informativas de acciones:\n"
            "- Preguntas con 'donde', 'como', 'que', 'cual', 'cuanto' = info_general (busca informacion)\n"
            "- Frases con 'quiero X', 'deseo X', 'necesito X', 'voy a X' = accion concreta\n\n"
            "EJEMPLOS:\n"
            "- 'Donde me inscribo?' = info_general (pregunta por el portal, no quiere empezar ahora)\n"
            "- 'Quiero inscribirme' = inscripcion (accion de iniciar flujo)\n"
            "- 'Cuales son los requisitos?' = info_general\n"
            "- 'Cuando es el examen?' = fechas\n"
            "- 'Cuanto cuesta?' = pago\n"
            "- 'Hablar con asesor' = queja_derivar\n"
            "- 'Mis resultados' = resultados\n\n"
            f"Intenciones validas: {', '.join(intents)}\n\n"
            "Responde SOLO con JSON valido en una linea: {\"intent\": \"...\", \"confidence\": 0.0-1.0}\n\n"
            f"Consulta del postulante: {user_message}"
        )
        try:
            r = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30.0,
            )
            r.raise_for_status()
            data = json.loads(r.json()["response"])
            intent = data.get("intent", "info_general")
            if intent not in intents:
                intent = "info_general"
            conf = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            return intent, conf
        except Exception as e:
            log.warning(f"Fallback en clasificacion: {e}")
            return "info_general", 0.3
