"""Router de intencion + reglas heuristicas de pre-filtro."""
import re

from app.agents.prompts import INTENT_LIST
from app.llm import get_llm

HEURISTICS = {
    "saludo": [r"^\s*(hola|hi|buenos d[i?]as|buenas tardes|buenas noches|gracias|chau|adi[o?]s)[\s!.?,]*$"],
    "queja_derivar": [
        r"\b(hablar con|asesor|persona|humano|agente|representante)\b",
        r"\b(reclamo|queja|molesto|molesta|frustrad|no (puedo|logro)|no funciona)\b",
    ],
    # Solo intencion CLARA de iniciar una inscripcion, no preguntas informativas
    "inscripcion": [
        r"\b(quiero|deseo|necesito|voy a) (inscribir|registrar|postular|aplicar)",
        r"\bme gustar[i?]a (inscribir|registrar|postular)",
        r"\b(empezar|iniciar|comenzar|arrancar) (mi |la |una |el proceso de )?inscripci[o?]n",
        r"\b(inscribir|registrar)me\b",
    ],
    "pago": [r"\b(pago|pagar|monto|costo|derecho de admisi[o?]n|cu[a?]nto cuesta)\b"],
    "resultados": [r"\b(resultado|ingres[e?]|aprob|puntaje|nota|pas[e?])\b"],
    "fechas": [r"\b(cu[a?]ndo|fecha|cronograma|calendario|plazo|vence)\b"],
    "canales": [r"\b(examen|canal|ponderaci[o?]n|asignaturas?|materias?)\b"],
    "modalidades": [r"\b(modalidad(es)?|traslado|primeros puestos|discapacidad|deportista|beca)\b"],
}


def classify(user_message: str) -> tuple[str, float, str]:
    text = user_message.lower().strip()
    for intent, patterns in HEURISTICS.items():
        for p in patterns:
            if re.search(p, text):
                return intent, 0.85, "heuristic"
    intent, conf = get_llm().classify_intent(user_message, INTENT_LIST)
    return intent, conf, "llm"


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
