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
    try:
        db.rollback()
    except Exception:
        pass

    # --- Fase 1: persistir sesion y mensaje del usuario ---
    if req.session_id:
        session = db.get(SessionModel, req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")
    else:
        session = SessionModel(channel=req.channel)
        db.add(session)
        db.flush()

    if req.dni:
        session.dni = req.dni
        session.identity_level = "authenticated"

    user_msg = Message(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()  # Persiste sesion + mensaje del usuario

    session_id = session.id
    session = db.get(SessionModel, session_id)  # re-fetch

    recent = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in recent[:-1]]

    # --- Fase 2: orquestar y procesar ---
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
    except Exception:
        log.exception("Fallo del orquestador")
        try:
            db.rollback()
        except Exception:
            pass
        session = db.get(SessionModel, session_id) or session
        result = {
            "reply": "Lo siento, tengo un problema tecnico. Puedes intentar nuevamente o contactar al 964 123 456.",
            "citations": [],
            "agent": "error",
            "confidence": 0.0,
            "requires_handoff": True,
            "phase": session.current_phase if session else "atencion",
            "intent": None,
        }

    if "state_update" in result:
        state.update(result["state_update"])

    # --- Fase 3: persistir respuesta del asistente ---
    try:
        session.state = state
        session.current_phase = result.get("phase", session.current_phase)
        session.current_intent = result.get("intent", session.current_intent)
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
    except Exception:
        log.exception("Fallo al persistir respuesta del asistente")
        try:
            db.rollback()
        except Exception:
            pass

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
