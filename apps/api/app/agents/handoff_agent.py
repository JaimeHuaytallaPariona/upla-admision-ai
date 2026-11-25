"""Agente de derivación: registra una observación y entrega información de contacto."""
from sqlalchemy.orm import Session

from app.models.db_models import Observation


class HandoffAgent:
    def __init__(self, db: Session):
        self.db = db

    def run(self, user_message: str, history: list[dict], session_id: str, reason: str = "user_requested") -> dict:
        try:
            obs = Observation(
                session_id=session_id,
                query=user_message,
                reason=reason,
                status="pending",
            )
            self.db.add(obs)
            self.db.commit()
        except Exception:
            self.db.rollback()

        reply = (
            "Entiendo. Voy a derivarte con un asesor de la Oficina de Admisión. "
            "Nuestro horario de atención es lunes a viernes de 8:00 a 17:00.\n\n"
            "Puedes contactarnos por:\n"
            "• WhatsApp Oficina de Admisión: 964 123 456\n"
            "• Correo: admision@upla.edu.pe\n"
            "• Presencial: Av. Giráldez 231, Huancayo\n\n"
            "Ya registré tu consulta para que un asesor retome contigo. ¿Prefieres que te contactemos por teléfono o correo?"
        )
        return {
            "reply": reply,
            "citations": [],
            "agent": "handoff",
            "confidence": 1.0,
            "requires_handoff": True,
            "handoff_target": "admision",
            "quick_replies": ["Prefiero WhatsApp", "Prefiero correo", "Volver al asistente"],
        }
