"""Agente de resultados: consulta por DNI con datos sintéticos."""
import re

from sqlalchemy.orm import Session

from app.mock.resultados import consultar_resultado


def _extract_dni(text: str) -> str | None:
    m = re.search(r"\b(\d{8})\b", text)
    return m.group(1) if m else None


class ResultsAgent:
    def __init__(self, db: Session):
        self.db = db

    def run(self, user_message: str, history: list[dict], state: dict) -> dict:
        dni = state.get("dni") or _extract_dni(user_message)
        if not dni:
            return {
                "reply": (
                    "Para consultar tus resultados necesito tu DNI (8 dígitos). "
                    "Es un dato que solo usamos para verificar tu inscripción."
                ),
                "citations": [],
                "agent": "results",
                "confidence": 0.95,
                "requires_handoff": False,
                "state_update": {"awaiting": "dni"},
            }

        resultado = consultar_resultado(dni)

        if not resultado:
            return {
                "reply": (
                    f"No encontré una inscripción activa con el DNI {dni} en el proceso actual. "
                    "Verifica que el DNI sea correcto o, si recién te inscribiste, considera que se refleja al día siguiente. "
                    "¿Quieres iniciar una inscripción ahora?"
                ),
                "citations": [],
                "agent": "results",
                "confidence": 0.9,
                "requires_handoff": False,
                "state_update": {"dni": dni},
                "quick_replies": ["Quiero inscribirme", "Hablar con un asesor"],
            }

        if resultado["estado"] == "en_proceso":
            reply = (
                f"Hola {resultado['nombres']}. Tu inscripción está registrada "
                f"(código {resultado['codigo']}) pero aún no se publican resultados de tu proceso. "
                f"La publicación oficial es el {resultado['fecha_resultados']}."
            )
        elif resultado["estado"] == "ingreso":
            reply = (
                f"¡Felicitaciones, {resultado['nombres']}! INGRESASTE a {resultado['carrera']} "
                f"con un puntaje de {resultado['puntaje']}/100, ocupando el puesto {resultado['puesto']}. "
                "Tu matrícula se abre el 10 de marzo; te enviaremos el detalle al correo que registraste."
            )
        else:  # no_ingreso
            reply = (
                f"Hola {resultado['nombres']}. Lamento informarte que no alcanzaste el puntaje mínimo "
                f"para {resultado['carrera']} en este proceso (tu puntaje fue {resultado['puntaje']}/100). "
                "Te animamos a postular en el próximo examen. ¿Quieres información sobre fechas del próximo proceso?"
            )

        return {
            "reply": reply,
            "citations": [],
            "agent": "results",
            "confidence": 0.98,
            "requires_handoff": False,
            "state_update": {"dni": dni, "identity_level": "authenticated"},
            "quick_replies": (
                ["Siguientes pasos para matrícula"] if resultado["estado"] == "ingreso"
                else ["Fechas del próximo proceso"]
            ),
        }
