"""Agente RAG: responde consultas informativas citando el Reglamento."""
import re

from sqlalchemy.orm import Session

from app.agents.prompts import SYSTEM_RAG
from app.llm import get_llm
from app.rag.retriever import Retriever, format_context


def detect_modalidad(text: str) -> str | None:
    t = text.lower()
    mapping = {
        "regular": "regular",
        "segunda carrera": "segunda_carrera",
        "traslado externo": "traslado_externo",
        "traslado interno": "traslado_interno",
        "primeros puestos": "primeros_puestos",
        "primer puesto": "primeros_puestos",
        "deportista": "deportistas_calificados",
        "deportistas": "deportistas_calificados",
        "discapacidad": "personas_con_discapacidad",
        "egresado": "egresados_institutos",
        "institut": "egresados_institutos",
        "mayores": "mayores_30",
        "primera selecci": "primera_seleccion",
        "oficiales": "oficiales_ffaa_ffpp",
        "suboficiales": "suboficiales_ffaa_ffpp",
        "beca oportunidad": "beca_oportunidad",
    }
    for k, v in mapping.items():
        if k in t:
            return v
    return None


def detect_canal(text: str) -> str | None:
    t = text.lower()
    # Por carrera
    carreras = {
        "I": ["administraci", "contabil", "econom", "turismo"],
        "II": ["ingenier", "arquitect", "sistemas", "civil", "mec", "ambient"],
        "III": ["enfermer", "farmac", "obstetr", "nutric", "psicolog", "tecnolog"],
        "IV": ["derecho", "educaci", "idiomas", "comunicaci"],
        "V": ["medicin", "odontolog"],
    }
    for canal, kws in carreras.items():
        for k in kws:
            if k in t:
                return canal
    # Explícito
    m = re.search(r"canal\s+(i{1,3}|iv|v)\b", t)
    if m:
        return m.group(1).upper()
    return None


class RAGAgent:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = Retriever(db)
        self.llm = get_llm()

    def run(self, user_message: str, history: list[dict], sensitivity_max: str = "public") -> dict:
        modalidad = detect_modalidad(user_message)
        canal = detect_canal(user_message)

        chunks = self.retriever.retrieve(
            query=user_message,
            modalidad=modalidad,
            canal=canal,
            sensitivity_max=sensitivity_max,
        )

        context = format_context(chunks)
        avg_score = sum(c["score"] for c in chunks) / len(chunks) if chunks else 0.0

        prompt_messages = history[-6:] + [
            {
                "role": "user",
                "content": (
                    f"FUENTES RECUPERADAS:\n{context}\n\n"
                    f"CONSULTA DEL POSTULANTE:\n{user_message}"
                ),
            }
        ]

        reply = self.llm.complete(system=SYSTEM_RAG, messages=prompt_messages, max_tokens=600)

        citations = [
            {
                "source": "Reglamento General de Admisión",
                "article": (c["metadata"] or {}).get("article"),
                "citation": c.get("citation", ""),
                "chunk_id": c["id"],
                "score": c["score"],
            }
            for c in chunks[:3]
            if c.get("citation")
        ]

        return {
            "reply": reply,
            "citations": citations,
            "agent": "rag",
            "confidence": round(min(avg_score + 0.1, 0.99), 3),
            "requires_handoff": avg_score < 0.45,
            "chunks_used": [c["id"] for c in chunks[:3]],
        }
