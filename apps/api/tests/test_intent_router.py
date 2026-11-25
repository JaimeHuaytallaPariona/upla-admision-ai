"""Tests del clasificador de intenciones heurístico (no requiere LLM)."""
from app.agents.intent_router import classify, intent_to_agent


def test_saludo():
    intent, conf, mech = classify("Hola, buenos días")
    assert intent == "saludo"
    assert mech == "heuristic"
    assert conf > 0.5


def test_inscripcion():
    intent, conf, mech = classify("Quiero inscribirme a la universidad")
    assert intent == "inscripcion"
    assert mech == "heuristic"


def test_pago():
    intent, _, _ = classify("¿Cuánto cuesta el derecho de admisión?")
    assert intent == "pago"


def test_derivar():
    intent, _, _ = classify("Necesito hablar con una persona")
    assert intent == "queja_derivar"


def test_fechas():
    intent, _, _ = classify("¿Cuándo es el próximo examen?")
    assert intent == "fechas"


def test_intent_to_agent_mapping():
    assert intent_to_agent("inscripcion") == "inscription"
    assert intent_to_agent("canales") == "exam"
    assert intent_to_agent("resultados") == "results"
    assert intent_to_agent("queja_derivar") == "handoff"
    assert intent_to_agent("saludo") == "greeting"
