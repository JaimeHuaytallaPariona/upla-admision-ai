"""Router de intención + reglas heurísticas de pre-filtro."""
import re
from typing import Any

from app.agents.prompts import INTENT_LIST
from app.llm import get_llm

# Palabras clave que disparan intenciones de forma determinística (más barato que LLM).
HEURISTICS = {
    "saludo": [r"^\s*(hola|hi|buenos d[ií]as|buenas tardes|buenas noches|gracias|chau|adi[oó]s)\b"],
    "queja_derivar": [
        r"\b(hablar con|asesor|persona|humano|agente|representante)\b",
        r"\b(reclamo|queja|molesto|molesta|frustrad|no (puedo|logro)|no funciona)\b",
    ],
    "inscripcion": [
        r"\b(inscribir|inscripci[oó]n|registrar|postular|aplicar)\b",
    ],
    "pago": [r"\b(pago|pagar|monto|costo|derecho de admisi[oó]n|cu[aá]nto cuesta)\b"],
    "resultados": [r"\b(resultado|ingres[eé]|aprob|puntaje|nota|pas[eé])\b"],
    "fechas": [r"\b(cu[aá]ndo|fecha|cronograma|calendario|plazo|vence)\b"],
    "canales": [r"\b(examen|canal|ponderaci[oó]n|asignaturas?|materias?)\b"],
    "modalidades": [r"\b(modalidad(es)?|traslado|primeros puestos|discapacidad|deportista|beca)\b"],
}


def classify(user_message: str) -> tuple[str, float, str]:
    """Clasifica la intención. Retorna (intent, confidence, mecanismo)."""
    text = user_message.lower().strip()

    # 1) Heurística primero (barato y determinístico)
    for intent, patterns in HEURISTICS.items():
        for p in patterns:
            if re.search(p, text):
                return intent, 0.85, "heuristic"

    # 2) Fallback a LLM
    intent, conf = get_llm().classify_intent(user_message, INTENT_LIST)
    return intent, conf, "llm"


# Mapeo intención → agente
INTENT_TO_AGENT = {
    "info_general": "rag",
    "modalidades": "rag",
    "canales": "exam",
    "fechas": "rag",
    "pago": "rag",
    "beca": "rag",
    "inscripcion": "inscription",
    "resultados": "results",
    "matricula": "matricula",
    "queja_derivar": "handoff",
    "saludo": "greeting",
    "fuera_ambito": "handoff",
}


def intent_to_agent(intent: str) -> str:
    return INTENT_TO_AGENT.get(intent, "rag")
