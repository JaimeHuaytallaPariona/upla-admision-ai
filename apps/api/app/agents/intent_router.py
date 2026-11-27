"""Router de intencion + reglas heuristicas de pre-filtro.

Estrategia: normalizamos el texto del usuario a minusculas sin acentos antes
de matchear, asi todos los patrones quedan en ASCII simple y evitamos lios
de codificacion Unicode (NFC vs NFD, char classes con acentos, etc.).
"""
import re
import unicodedata

from app.agents.prompts import INTENT_LIST
from app.llm import get_llm


def _strip_accents(s: str) -> str:
    """Quita tildes y diacriticos. 'cuando' <- 'cuando'/'cuándo'."""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    return _strip_accents(s.lower().strip())


# Tokens que componen un saludo. Un mensaje es saludo si TODAS sus palabras
# (tras quitar puntuacion) estan en este set y hay entre 1 y 5 palabras.
_GREETING_TOKENS = {
    "hola", "hi", "hey", "holi", "holis",
    "buenos", "buenas", "buen",
    "dia", "dias", "tarde", "tardes", "noche", "noches",
    "que", "tal", "como", "estas", "esta", "vas",
    "gracias", "muchas",
    "chau", "adios", "bye",
    "hasta", "luego", "pronto", "nos", "vemos",
    "saludos", "cordial", "cordiales",
}
_SPLIT_RE = re.compile(r"[^a-z]+")


def _is_greeting(normalized_text: str) -> bool:
    tokens = [t for t in _SPLIT_RE.split(normalized_text) if t]
    if not tokens or len(tokens) > 5:
        return False
    return all(t in _GREETING_TOKENS for t in tokens)


# Patrones por intencion, aplicados sobre texto NORMALIZADO (minusculas, sin acentos).
HEURISTICS = {
    "queja_derivar": [
        r"\b(hablar con|asesor|persona|humano|agente|representante)\b",
        r"\b(reclamo|queja|molesto|molesta|frustrad|no (puedo|logro)|no funciona)\b",
    ],
    # Solo intencion CLARA de iniciar una inscripcion, no preguntas informativas
    "inscripcion": [
        r"\b(quiero|deseo|necesito|voy a) (inscribir|registrar|postular|aplicar)",
        r"\bme gustaria (inscribir|registrar|postular)",
        r"\b(empezar|iniciar|comenzar|arrancar) (mi |la |una |el proceso de )?inscripcion",
        r"\b(inscribir|registrar)me\b",
    ],
    # fechas ANTES que canales: "cuando es el examen" -> fechas, no canales
    "fechas": [
        r"\b(cuando|fecha|fechas|cronograma|calendario|plazo|vence|a que hora|en que fecha|proximo examen|proxima|proximo)\b",
    ],
    "pago": [
        r"\b(pago|pagar|monto|costo|precio|tarifa|inversion|derecho de admision|cuanto cuesta|cuanto es|cuanto pago)\b",
    ],
    "resultados": [
        r"\b(resultado|resultados|ingrese|aprob|puntaje|nota|pase)\b",
    ],
    "canales": [
        r"\b(canal|ponderacion|asignaturas?|materias?|composicion del examen|que entra|que materias)\b",
    ],
    "modalidades": [
        r"\b(modalidad(es)?|traslado|primeros puestos|discapacidad|deportista|beca)\b",
    ],
}


def classify(user_message: str) -> tuple[str, float, str]:
    text = _norm(user_message)

    # Saludo primero (tokenizacion explicita en vez de regex complejo)
    if _is_greeting(text):
        return "saludo", 0.95, "heuristic"

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
