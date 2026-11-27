"""Agente de inscripcion: conduce la captura de datos paso a paso."""
import re
import uuid

from sqlalchemy.orm import Session

from app.llm import get_llm
from app.models.db_models import Inscripcion
from app.mock.catalogo_carreras import CARRERAS_BY_CANAL, canal_de_carrera
from app.mock.catalogo_modalidades import MODALIDADES

# Pasos del flujo de inscripcion
STEPS = [
    ("dni", "Para iniciar tu inscripcion, necesito tu DNI (8 digitos). Me lo puedes compartir?"),
    ("nombres", "Gracias. Cuales son tus nombres? (Solo tus nombres, sin apellidos. Ejemplo: Maria Alejandra)"),
    ("apellidos", "Y tus apellidos? (Paterno y materno. Ejemplo: Quispe Yauri)"),
    ("email", "Perfecto. Cual es tu correo electronico? Ahi te enviaremos las notificaciones oficiales."),
    ("telefono", "Un numero de celular con WhatsApp donde podamos contactarte?"),
    ("modalidad", "En que modalidad vas a postular? (Ejemplo: Regular, Primeros Puestos, Traslado Externo)"),
    ("carrera", "A que carrera quieres postular?"),
    ("confirmacion", "Con esos datos ya puedo generar tu pre-inscripcion. Confirmas que todo esta correcto? (si/no)"),
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
    words = t.split()
    for canal, carreras in CARRERAS_BY_CANAL.items():
        for c in carreras:
            if any(w in c.lower() for w in words if len(w) > 5):
                return c
    return None


def _extract_nombres(text: str):
    """
    Si vienen 3 o mas palabras, asume que las ultimas 2 son apellidos y devuelve un dict
    con nombres y apellidos separados. Si vienen 1-2 palabras, retorna solo el texto.
    """
    if not text or any(c.isdigit() for c in text) or len(text.strip()) < 2:
        return None
    parts = text.strip().split()
    if len(parts) >= 4:
        return {"nombres": " ".join(parts[:-2]), "apellidos": " ".join(parts[-2:])}
    if len(parts) == 3:
        return {"nombres": parts[0], "apellidos": " ".join(parts[1:])}
    return " ".join(parts)


def _extract_apellidos(text: str) -> str | None:
    if not text or any(c.isdigit() for c in text) or len(text.strip()) < 2:
        return None
    return text.strip()


EXTRACTORS = {
    "dni": _extract_dni,
    "email": _extract_email,
    "telefono": _extract_phone,
    "modalidad": _extract_modalidad,
    "carrera": _extract_carrera,
    "nombres": _extract_nombres,
    "apellidos": _extract_apellidos,
}


class InscriptionAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm()

    def run(self, user_message: str, history: list[dict], state: dict) -> dict:
        inscripcion_data = state.get("inscripcion", {})
        current_step = state.get("inscripcion_step")

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

        extractor = EXTRACTORS.get(current_step, lambda t: t.strip() if t.strip() else None)
        extracted = extractor(user_message)

        if current_step == "confirmacion":
            if re.search(r"\b(si|confirmo|correcto|dale|ok)\b", user_message.lower()):
                return self._finalize(inscripcion_data, state)
            else:
                state["inscripcion_step"] = None
                state["inscripcion"] = {}
                return {
                    "reply": "Entendido, cancelo esta pre-inscripcion. Que dato quieres corregir o prefieres empezar de nuevo?",
                    "citations": [],
                    "agent": "inscription",
                    "confidence": 0.9,
                    "requires_handoff": False,
                    "state_update": {"inscripcion_step": None, "inscripcion": {}},
                }

        if not extracted:
            prompt = next((p for s, p in STEPS if s == current_step), "")
            return {
                "reply": f"No pude identificar el dato. Intenta nuevamente: {prompt}",
                "citations": [],
                "agent": "inscription",
                "confidence": 0.7,
                "requires_handoff": False,
                "state_update": state,
            }

        # Caso especial: si el usuario escribio nombre completo al pedir nombres,
        # auto-separamos y saltamos el paso de apellidos.
        if current_step == "nombres" and isinstance(extracted, dict):
            inscripcion_data["nombres"] = extracted["nombres"]
            inscripcion_data["apellidos"] = extracted["apellidos"]
            idx = STEP_ORDER.index("apellidos")
            next_step = STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None
            state["inscripcion_step"] = next_step
            state["inscripcion"] = inscripcion_data
            next_prompt = next((p for s, p in STEPS if s == next_step), "")
            return {
                "reply": (
                    f"Anotado: nombres = {extracted['nombres']}, apellidos = {extracted['apellidos']}. "
                    f"{next_prompt}"
                ),
                "citations": [],
                "agent": "inscription",
                "confidence": 0.95,
                "requires_handoff": False,
                "state_update": state,
            }

        inscripcion_data[current_step] = extracted
        if current_step == "carrera":
            canal = canal_de_carrera(extracted)
            if canal:
                inscripcion_data["canal"] = canal

        idx = STEP_ORDER.index(current_step)
        next_step = STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None
        state["inscripcion_step"] = next_step
        state["inscripcion"] = inscripcion_data

        if next_step == "confirmacion":
            summary = self._format_summary(inscripcion_data)
            return {
                "reply": f"Perfecto. Esto es lo que tengo:\n\n{summary}\n\nConfirmas que todo esta correcto? (si/no)",
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
        return "\n".join([
            f"- DNI: {data.get('dni', '-')}",
            f"- Nombres: {data.get('nombres', '-')}",
            f"- Apellidos: {data.get('apellidos', '-')}",
            f"- Correo: {data.get('email', '-')}",
            f"- Celular: {data.get('telefono', '-')}",
            f"- Modalidad: {data.get('modalidad', '-')}",
            f"- Carrera: {data.get('carrera', '-')}",
            f"- Canal: {data.get('canal', '-')}",
        ])

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
                f"Listo! Tu pre-inscripcion se genero con el codigo **{codigo}**.\n\n"
                "Siguientes pasos:\n"
                "1. Subir tus documentos escaneados (DNI, constancia de estudios, foto) en https://admision.upla.edu.pe/documentos\n"
                "2. Realizar el pago del derecho de admision en el Banco de la Nacion (codigo 00231).\n"
                "3. Agendar tu examen segun tu canal.\n\n"
                "Te enviamos el detalle al correo que registraste. Hay algo mas en lo que te pueda ayudar?"
            ),
            "citations": [],
            "agent": "inscription",
            "confidence": 0.98,
            "requires_handoff": False,
            "state_update": state,
        }

