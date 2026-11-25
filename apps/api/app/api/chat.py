"""Endpoint principal de chat. Entry-point del orquestador multiagente."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator
from app.db import get_db
from app.models.db_models import Message, Session as SessionModel
from app.models.schemas import ChatRequest, ChatResponse, Citation

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def post_message(req: ChatRequest, db: Session = Depends(get_db)):
    # Resolver sesión
    if req.session_id:
        session = db.get(SessionModel, req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
    else:
        session = SessionModel(channel=req.channel)
        db.add(session)
        db.flush()

    # Si el request trae DNI, promover identidad
    if req.dni:
        session.dni = req.dni
        session.identity_level = "authenticated"

    # Persistir mensaje entrante
    user_msg = Message(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    db.flush()

    # Historia reciente para contexto del LLM
    recent = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in recent[:-1]]

    # Invocar orquestador
    state = dict(session.state or {})
    orch = Orchestrator(db)
    try:
        result = orch.handle(
            user_message=req.message,
            history=history,
            session_state=state,
            session_id=session.id,
            identity_level=session.identity_level,
        )
    except Exception as e:
        log.exception("Fallo del orquestador")
        result = {
            "reply": f"Lo siento, tengo un problema técnico. Puedes intentar nuevamente o contactar al 964 123 456.",
            "citations": [],
            "agent": "error",
            "confidence": 0.0,
            "requires_handoff": True,
            "phase": session.current_phase,
            "intent": None,
        }

    # Actualizar estado y fase
    if "state_update" in result:
        state.update(result["state_update"])
    session.state = state
    session.current_phase = result.get("phase", session.current_phase)
    session.current_intent = result.get("intent", session.current_intent)

    # Persistir respuesta
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=result["reply"],
        agent=result.get("agent"),
        citations=result.get("citations"),
        confidence=result.get("confidence"),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        session_id=session.id,
        reply=result["reply"],
        citations=[Citation(**c) if not isinstance(c, Citation) else c for c in result.get("citations", [])],
        agent=result.get("agent", "unknown"),
        phase=session.current_phase,
        intent=session.current_intent,
        confidence=result.get("confidence", 0.0),
        requires_handoff=result.get("requires_handoff", False),
        quick_replies=result.get("quick_replies", []),
    )
