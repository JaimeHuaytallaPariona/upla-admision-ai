"""Agente de bienvenida y despedida."""
from sqlalchemy.orm import Session


class GreetingAgent:
    def __init__(self, db: Session):
        self.db = db

    def run(self, user_message: str, history: list[dict]) -> dict:
        text = user_message.lower()
        if any(w in text for w in ["gracias", "chau", "adi", "nos vemos", "hasta"]):
            reply = (
                "¡Gracias a ti! Si necesitas más ayuda durante el proceso de admisión, estoy acá 24/7. "
                "¡Mucha suerte con tu postulación a la UPLA! 🎓"
            )
            quick = []
        else:
            reply = (
                "¡Hola! Soy el asistente virtual de admisión de la UPLA. "
                "Te puedo ayudar a:\n"
                "• Conocer las modalidades y requisitos para postular\n"
                "• Ver las asignaturas y ponderación de tu examen\n"
                "• Iniciar tu inscripción paso a paso\n"
                "• Consultar tus resultados\n"
                "• Derivarte con un asesor humano si lo necesitas\n\n"
                "¿En qué te puedo ayudar hoy?"
            )
            quick = [
                "Quiero inscribirme",
                "¿Qué modalidades hay?",
                "¿Cuándo es el examen?",
                "Hablar con un asesor",
            ]
        return {
            "reply": reply,
            "citations": [],
            "agent": "greeting",
            "confidence": 0.99,
            "requires_handoff": False,
            "quick_replies": quick,
        }
