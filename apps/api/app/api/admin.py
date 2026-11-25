"""Endpoints del panel de administración / monitoreo del asistente."""
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.db_models import Inscripcion, Message, Observation
from app.models.db_models import Session as SessionModel
from app.models.schemas import ObservationOut, PanelMetrics

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=PanelMetrics)
def metrics(db: Session = Depends(get_db)):
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    sessions_total = db.query(func.count(SessionModel.id)).scalar() or 0
    sessions_today = db.query(func.count(SessionModel.id)).filter(SessionModel.created_at >= today_start).scalar() or 0
    messages_total = db.query(func.count(Message.id)).scalar() or 0
    observations_pending = db.query(func.count(Observation.id)).filter(Observation.status == "pending").scalar() or 0
    insc_iniciadas = db.query(func.count(Inscripcion.id)).scalar() or 0
    insc_conf = db.query(func.count(Inscripcion.id)).filter(Inscripcion.estado == "confirmada").scalar() or 0
    avg_conf = db.query(func.avg(Message.confidence)).filter(Message.confidence.isnot(None)).scalar() or 0.0

    intents = [s.current_intent for s in db.query(SessionModel).all() if s.current_intent]
    top = Counter(intents).most_common(5)

    return PanelMetrics(
        sessions_total=int(sessions_total),
        sessions_today=int(sessions_today),
        messages_total=int(messages_total),
        observations_pending=int(observations_pending),
        inscripciones_iniciadas=int(insc_iniciadas),
        inscripciones_confirmadas=int(insc_conf),
        avg_confidence=round(float(avg_conf), 3),
        top_intents=[{"intent": i, "count": c} for i, c in top],
    )


@router.get("/observations", response_model=list[ObservationOut])
def list_observations(status: str = "pending", db: Session = Depends(get_db)):
    q = db.query(Observation).filter(Observation.status == status).order_by(Observation.created_at.desc()).limit(50)
    return [
        ObservationOut(
            id=o.id,
            session_id=o.session_id,
            query=o.query,
            reason=o.reason,
            status=o.status,
            created_at=o.created_at,
        )
        for o in q
    ]


@router.get("/inscripciones")
def list_inscripciones(db: Session = Depends(get_db)):
    rows = db.query(Inscripcion).order_by(Inscripcion.created_at.desc()).limit(50).all()
    return [
        {
            "codigo": r.codigo_inscripcion,
            "dni": r.dni,
            "nombres": f"{r.nombres} {r.apellidos}",
            "email": r.email,
            "modalidad": r.modalidad,
            "carrera": r.carrera,
            "canal": r.canal,
            "estado": r.estado,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    rows = db.query(SessionModel).order_by(SessionModel.updated_at.desc()).limit(50).all()
    return [
        {
            "id": s.id,
            "channel": s.channel,
            "identity_level": s.identity_level,
            "current_phase": s.current_phase,
            "current_intent": s.current_intent,
            "message_count": len(s.messages),
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in rows
    ]
