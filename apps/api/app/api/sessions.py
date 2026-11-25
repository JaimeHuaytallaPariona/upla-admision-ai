"""Endpoints de sesiones (lectura de historial)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.db_models import Message, Session as SessionModel
from app.models.schemas import MessageOut, SessionSummary

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=SessionSummary)
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return SessionSummary(
        id=s.id,
        channel=s.channel,
        identity_level=s.identity_level,
        current_phase=s.current_phase,
        current_intent=s.current_intent,
        message_count=len(s.messages),
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    msgs = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            agent=m.agent,
            citations=m.citations,
            confidence=m.confidence,
            created_at=m.created_at,
        )
        for m in msgs
    ]
