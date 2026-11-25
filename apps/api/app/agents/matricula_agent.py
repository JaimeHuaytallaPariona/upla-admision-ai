"""Agente de matrícula: fuera del ámbito de admisión. Informa y deriva."""
from sqlalchemy.orm import Session


class MatriculaAgent:
    def __init__(self, db: Session):
        self.db = db

    def run(self, user_message: str, history: list[dict]) -> dict:
        reply = (
            "La matrícula ya es parte del proceso académico, fuera del alcance de la Oficina de Admisión. "
            "En líneas generales, una vez que ingresas, se habilita el aula virtual con el cronograma y los enlaces de pago "
            "de la Oficina de Servicios Académicos.\n\n"
            "Para el detalle específico de tu caso, te derivo con la Oficina de Servicios Académicos:\n"
            "• Teléfono: (064) 481430 anexo 219\n"
            "• Correo: servicios.academicos@upla.edu.pe\n"
            "• Horario: lunes a viernes, 8:00 a 17:00"
        )
        return {
            "reply": reply,
            "citations": [],
            "agent": "matricula",
            "confidence": 0.95,
            "requires_handoff": True,
            "handoff_target": "servicios_academicos",
            "quick_replies": ["Volver al menú", "Consultar resultados"],
        }
