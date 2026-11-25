"""Agente de examen: información sobre canales, ponderación, simulacros, cronograma."""
from sqlalchemy.orm import Session

from app.agents.prompts import SYSTEM_EXAMEN
from app.agents.rag_agent import detect_canal
from app.llm import get_llm
from app.mock.cronograma import CRONOGRAMA
from app.rag.retriever import Retriever, format_context


class ExamAgent:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = Retriever(db)
        self.llm = get_llm()

    def run(self, user_message: str, history: list[dict]) -> dict:
        canal = detect_canal(user_message)

        if not canal:
            return {
                "reply": (
                    "Para decirte las asignaturas y la ponderación de tu examen, dime a qué carrera estás postulando. "
                    "La UPLA agrupa sus 25 carreras en 5 canales, y cada uno tiene su propio examen."
                ),
                "citations": [],
                "agent": "exam",
                "confidence": 0.9,
                "requires_handoff": False,
                "quick_replies": [
                    "Ingeniería de Sistemas", "Medicina Humana", "Enfermería",
                    "Derecho", "Administración",
                ],
            }

        chunks = self.retriever.retrieve(
            query=f"ponderación canal {canal} asignaturas examen",
            canal=canal,
            top_k=3,
        )

        context = format_context(chunks)
        cronograma_text = (
            f"\n\nCRONOGRAMA (próximo proceso):\n"
            f"• Simulacro: {CRONOGRAMA['simulacro']}\n"
            f"• Examen: {CRONOGRAMA['examen']}\n"
            f"• Resultados: {CRONOGRAMA['resultados']}"
        )

        msgs = history[-4:] + [{
            "role": "user",
            "content": f"FUENTES:\n{context}{cronograma_text}\n\nCONSULTA: {user_message}",
        }]
        reply = self.llm.complete(system=SYSTEM_EXAMEN, messages=msgs, max_tokens=500)

        citations = [
            {
                "source": "Reglamento General de Admisión",
                "article": (c["metadata"] or {}).get("article"),
                "citation": c.get("citation", ""),
                "chunk_id": c["id"],
                "score": c["score"],
            }
            for c in chunks[:2]
        ]

        return {
            "reply": reply,
            "citations": citations,
            "agent": "exam",
            "confidence": 0.9,
            "requires_handoff": False,
            "quick_replies": ["Quiero inscribirme", "¿Cuándo es el pago?", "¿Dónde es el examen?"],
        }
