"""Orquestador multiagente. Máquina de estados simple con routing por intención."""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.exam_agent import ExamAgent
from app.agents.greeting_agent import GreetingAgent
from app.agents.handoff_agent import HandoffAgent
from app.agents.inscription_agent import InscriptionAgent
from app.agents.intent_router import classify, intent_to_agent
from app.agents.matricula_agent import MatriculaAgent
from app.agents.rag_agent import RAGAgent
from app.agents.results_agent import ResultsAgent

log = logging.getLogger(__name__)

# Intenciones → fase del embudo (para telemetría y UI)
INTENT_TO_PHASE = {
    "saludo": "atencion",
    "info_general": "atencion",
    "modalidades": "atencion",
    "canales": "examen",
    "fechas": "atencion",
    "pago": "inscripcion",
    "beca": "atencion",
    "inscripcion": "inscripcion",
    "resultados": "resultados",
    "matricula": "matricula",
    "queja_derivar": "atencion",
    "fuera_ambito": "atencion",
}


class Orchestrator:
    def __init__(self, db: Session):
        self.db = db

    def handle(
        self,
        user_message: str,
        history: list[dict],
        session_state: dict,
        session_id: str,
        identity_level: str = "anonymous",
    ) -> dict:
        """
        Entrada principal. Recibe el mensaje y el estado persistido.
        Retorna un dict con reply, agent, phase, intent, confidence, state_update.
        """
        # Si hay un flujo de inscripción en curso, no re-clasificamos: continuamos.
        if session_state.get("inscripcion_step") is not None:
            session_state["session_id"] = session_id
            agent = InscriptionAgent(self.db)
            result = agent.run(user_message, history, session_state)
            result.setdefault("phase", "inscripcion")
            result.setdefault("intent", "inscripcion")
            return result

        # Si hay un awaiting específico (ej: DNI para resultados), seguimos con ese agente.
        awaiting = session_state.get("awaiting")
        if awaiting == "dni":
            session_state.pop("awaiting", None)
            agent = ResultsAgent(self.db)
            result = agent.run(user_message, history, session_state)
            result.setdefault("phase", "resultados")
            result.setdefault("intent", "resultados")
            return result

        # Clasificar intención
        intent, confidence, mechanism = classify(user_message)
        log.info(f"Intent clasificado: {intent} ({confidence:.2f} via {mechanism})")

        agent_name = intent_to_agent(intent)
        phase = INTENT_TO_PHASE.get(intent, "atencion")

        # Sensibilidad para RAG según nivel de identidad
        sensitivity_max = "authenticated_only" if identity_level == "authenticated" else "public"

        if agent_name == "greeting":
            result = GreetingAgent(self.db).run(user_message, history)
        elif agent_name == "rag":
            result = RAGAgent(self.db).run(user_message, history, sensitivity_max=sensitivity_max)
        elif agent_name == "exam":
            result = ExamAgent(self.db).run(user_message, history)
        elif agent_name == "inscription":
            session_state["session_id"] = session_id
            result = InscriptionAgent(self.db).run(user_message, history, session_state)
        elif agent_name == "results":
            result = ResultsAgent(self.db).run(user_message, history, session_state)
        elif agent_name == "matricula":
            result = MatriculaAgent(self.db).run(user_message, history)
        elif agent_name == "handoff":
            reason = "user_requested" if intent == "queja_derivar" else "out_of_scope"
            result = HandoffAgent(self.db).run(user_message, history, session_id, reason=reason)
        else:
            result = RAGAgent(self.db).run(user_message, history, sensitivity_max=sensitivity_max)

        result.setdefault("phase", phase)
        result.setdefault("intent", intent)
        result.setdefault("confidence", confidence)
        return result
