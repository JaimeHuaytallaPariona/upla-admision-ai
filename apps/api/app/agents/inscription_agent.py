"""Agente de inscripción: conduce la captura de datos paso a paso."""
import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import SYSTEM_INSCRIPCION
from app.llm import get_llm
from app.models.db_models import Inscripcion
from app.mock.catalogo_carreras import CARRERAS_BY_CANAL, canal_de_carrera
from app.mock.catalogo_modalidades import MODALIDADES

# Pasos del flujo de inscripción
STEPS = [
    ("dni", "Para iniciar tu inscripción, necesito tu DNI (8 dígitos). ¿Me lo puedes compartir?"),
    ("nombres", "Gracias. ¿Cuáles son tus nombres completos?"),
    ("apellidos", "¿Y tus apellidos (paterno y materno)?"),
    ("email", "Perfecto. ¿Cuál es tu correo electrónico? Ahí te enviaremos las notificaciones oficiales."),
    ("telefono", "¿Un número de celular con WhatsApp donde podamos contactarte?"),
    ("modalidad", "¿En qué modalidad vas a postular? (ej: Regular, Primeros Puestos, Traslado Externo…)"),
    ("carrera", "¿A qué carrera quieres postular?"),
    ("confirmacion", "Con esos datos ya puedo generar tu pre-inscripción. ¿Confirmas que todo está correcto? (sí/no)"),
]

STEP_ORDER = [s[0] for s in STEPS]


def _extract_dni(text: str) -> str | None:
    m = re.search(r"\b(\d{8})\b", text)
    return m.group(1) if m else None


def _extract_email(text: str) -> str | None:
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"\b(9\d{8})\b", text)
    return m.group(1) if m else None


def _extract_modalidad(text: str) -> str | None:
    t = text.lower()
    for mod in MODALIDADES:
        if mod["match"].lower() in t:
            return mod["id"]
    return None


def _extract_carrera(text: str) -> str | None:
    t = text.lower()
    for canal, carreras in CARRERAS_BY_CANAL.items():
        for c in carreras:
            if c.lower() in t:
                return c
    # Match parcial
    words = t.split()
    for canal, carreras in CARRERAS_BY_CANAL.items():
        for c in carreras:
            if any(w in c.lower() for w in words if len(w) > 5):
                return c
    return None


EXTRACTORS = {
    "dni": _extract_dni,
    "email": _extract_email,
    "telefono": _extract_phone,
    "modalidad": _extract_modalidad,
    "carrera": _extract_carrera,
    "nombres": lambda t: t.strip() if len(t.strip()) >= 2 and not any(c.isdigit() for c in t) else None,
    "apellidos": lambda t: t.strip() if len(t.strip()) >= 2 and not any(c.isdigit() for c in t) else None,
}


class InscriptionAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm()

    def run(self, user_message: str, history: list[dict], state: dict) -> dict:
        inscripcion_data = state.get("inscripcion", {})
        current_step = state.get("inscripcion_step")

        # Si no hay paso actual, empezar por el primero que falta
        if current_step is None or current_step not in STEP_ORDER:
            current_step = next((s for s in STEP_ORDER if s not in inscripcion_data), "confirmacion")
            prompt = next((p for s, p in STEPS if s == current_step), "")
            state["inscripcion_step"] = current_step
            return {
                "reply": prompt,
                "citations": [],
                "agent": "inscription",
                "confidence": 0.95,
                "requires_handoff": False,
                "state_update": {"inscripcion_step": current_step, "inscripcion": inscripcion_data},
            }

        # Intentar extraer el dato del mensaje
        extractor = EXTRACTORS.get(current_step, lambda t: t.strip() if t.strip() else None)
        extracted = extractor(user_message)

        if current_step == "confirmacion":
            if re.search(r"\b(s[ií]|confirmo|correcto|dale|ok)\b", user_message.lower()):
                return self._finalize(inscripcion_data, state)
            else:
                state["inscripcion_step"] = None
                state["inscripcion"] = {}
                return {
                    "reply": "Entendido, cancelo esta pre-inscripción. ¿Qué dato quieres corregir o prefieres empezar de nuevo?",
                    "citations": [],
                    "agent": "inscription",
                    "confidence": 0.9,
                    "requires_handoff": False,
                    "state_update": {"inscripcion_step": None, "inscripcion": {}},
                }

        if not extracted:
            prompt = next((p for s, p in STEPS if s == current_step), "")
            return {
                "reply": f"No pude identificar el dato. {prompt}",
                "citations": [],
                "agent": "inscription",
                "confidence": 0.7,
                "requires_handoff": False,
                "state_update": state,
            }

        inscripcion_data[current_step] = extracted
        # Si capturó carrera, fijar canal
        if current_step == "carrera":
            canal = canal_de_carrera(extracted)
            if canal:
                inscripcion_data["canal"] = canal

        # Avanzar al siguiente paso
        idx = STEP_ORDER.index(current_step)
        next_step = STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None
        state["inscripcion_step"] = next_step
        state["inscripcion"] = inscripcion_data

        if next_step == "confirmacion":
            summary = self._format_summary(inscripcion_data)
            return {
                "reply": f"Perfecto. Esto es lo que tengo:\n\n{summary}\n\n¿Confirmas que todo está correcto? (sí/no)",
                "citations": [],
                "agent": "inscription",
                "confidence": 0.95,
                "requires_handoff": False,
                "state_update": state,
            }

        next_prompt = next((p for s, p in STEPS if s == next_step), "")
        return {
            "reply": f"Anotado: {current_step} = {extracted}. {next_prompt}",
            "citations": [],
            "agent": "inscription",
            "confidence": 0.95,
            "requires_handoff": False,
            "state_update": state,
        }

    def _format_summary(self, data: dict) -> str:
        lines = [
            f"• DNI: {data.get('dni', '-')}",
            f"• Nombres: {data.get('nombres', '-')} {data.get('apellidos', '')}",
            f"• Correo: {data.get('email', '-')}",
            f"• Celular: {data.get('telefono', '-')}",
            f"• Modalidad: {data.get('modalidad', '-')}",
            f"• Carrera: {data.get('carrera', '-')}",
            f"• Canal: {data.get('canal', '-')}",
        ]
        return "\n".join(lines)

    def _finalize(self, data: dict, state: dict) -> dict:
        codigo = f"UPLA-2026-{uuid.uuid4().hex[:6].upper()}"
        try:
            insc = Inscripcion(
                session_id=state.get("session_id", "demo"),
                codigo_inscripcion=codigo,
                dni=data["dni"],
                nombres=data["nombres"],
                apellidos=data["apellidos"],
                email=data["email"],
                telefono=data["telefono"],
                modalidad=data["modalidad"],
                carrera=data["carrera"],
                canal=data.get("canal", "I"),
                estado="documentos_pendientes",
            )
            self.db.add(insc)
            self.db.commit()
        except Exception:
            self.db.rollback()

        state["inscripcion_step"] = None
        state["inscripcion"] = {}
        state["last_codigo"] = codigo

        return {
            "reply": (
                f"¡Listo! Tu pre-inscripción se generó con el código **{codigo}**.\n\n"
                "Siguientes pasos:\n"
                "1. Subir tus documentos escaneados (DNI, constancia de estudios, foto) en https://admision.upla.edu.pe/documentos\n"
                "2. Realizar el pago del derecho de admisión en el Banco de la Nación (código 00231).\n"
                "3. Agendar tu examen según tu canal.\n\n"
                "Te enviamos el detalle al correo que registraste. ¿Hay algo más en lo que te pueda ayudar?"
            ),
            "citations": [],
            "agent": "inscription",
            "confidence": 0.98,
            "requires_handoff": False,
            "state_update": state,
        }
