"""Esquemas Pydantic de request/response."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    article: Optional[str] = None
    citation: str
    chunk_id: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    channel: Literal["web", "whatsapp"] = "web"
    message: str = Field(..., min_length=1, max_length=4000)
    dni: Optional[str] = None  # si el usuario se autentica


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    citations: list[Citation] = []
    agent: str
    phase: str
    intent: Optional[str] = None
    confidence: float
    requires_handoff: bool = False
    quick_replies: list[str] = []


class SessionSummary(BaseModel):
    id: str
    channel: str
    identity_level: str
    current_phase: str
    current_intent: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    agent: Optional[str] = None
    citations: Optional[list[dict]] = None
    confidence: Optional[float] = None
    created_at: datetime


class ObservationOut(BaseModel):
    id: str
    session_id: str
    query: str
    reason: str
    status: str
    created_at: datetime


class PanelMetrics(BaseModel):
    sessions_total: int
    sessions_today: int
    messages_total: int
    observations_pending: int
    inscripciones_iniciadas: int
    inscripciones_confirmadas: int
    avg_confidence: float
    top_intents: list[dict]
