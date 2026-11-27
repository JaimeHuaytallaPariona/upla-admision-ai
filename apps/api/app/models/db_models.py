"""Modelos de base de datos: sesiones, mensajes, chunks indexados y bandeja de observaciones."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

from app.config import get_settings

settings = get_settings()
Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    channel = Column(String, nullable=False, default="web")  # web, whatsapp
    identity_level = Column(String, nullable=False, default="anonymous")  # anonymous, authenticated
    dni = Column(String, nullable=True)
    postulante_data = Column(JSON, nullable=True)
    current_phase = Column(String, nullable=False, default="atencion")
    current_intent = Column(String, nullable=True)
    state = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    agent = Column(String, nullable=True)  # which agent produced this
    citations = Column(JSON, nullable=True)  # list of {source, article, citation}
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class KBChunk(Base):
    __tablename__ = "kb_chunks"

    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(settings.embedding_dim), nullable=False)
    chunk_metadata = Column("metadata", JSON, nullable=False)
    content_hash = Column(String, nullable=False)
    indexed_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Observation(Base):
    """Bandeja de observaciones — consultas no resueltas o que requieren intervención humana."""
    __tablename__ = "observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    query = Column(Text, nullable=False)
    reason = Column(String, nullable=False)  # low_confidence, user_requested, out_of_scope, sensitive
    status = Column(String, nullable=False, default="pending")  # pending, in_review, resolved
    assigned_to = Column(String, nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Inscripcion(Base):
    """Inscripciones capturadas por el asistente (para demo, se almacenan aquí)."""
    __tablename__ = "inscripciones"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    codigo_inscripcion = Column(String, nullable=False, unique=True, index=True)
    dni = Column(String, nullable=False, index=True)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    modalidad = Column(String, nullable=False)
    carrera = Column(String, nullable=False)
    canal = Column(String, nullable=False)
    estado = Column(String, nullable=False, default="iniciada")  # iniciada, documentos_pendientes, verificada, pago_pendiente, pagada, confirmada
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
