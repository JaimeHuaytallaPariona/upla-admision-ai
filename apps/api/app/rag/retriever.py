"""Recuperacion hibrida (semantica + filtros categoricos) contra pgvector."""
import logging
from typing import Any

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.rag.embedder import embed

log = logging.getLogger(__name__)


class Retriever:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        topic: str | None = None,
        modalidad: str | None = None,
        canal: str | None = None,
        sensitivity_max: str = "public",
    ) -> list[dict[str, Any]]:
        top_k = top_k or self.settings.rag_top_k
        q_vec = embed(query)

        if sensitivity_max == "public":
            allowed = ["public"]
        elif sensitivity_max == "authenticated_only":
            allowed = ["public", "authenticated_only"]
        else:
            allowed = ["public", "authenticated_only", "internal_only"]

        where = ["((metadata::jsonb)->>'sensitivity') IN :allowed"]
        params: dict[str, Any] = {"q": str(q_vec), "allowed": tuple(allowed), "k": top_k}

        if topic:
            where.append("((metadata::jsonb)->>'topic') = :topic")
            params["topic"] = topic
        if modalidad:
            where.append(
                "((metadata::jsonb)->'modalidades_aplicables' ? :modalidad OR "
                "(metadata::jsonb)->'modalidades_aplicables' ? 'todas')"
            )
            params["modalidad"] = modalidad
        if canal:
            where.append(
                "((metadata::jsonb)->'canales_aplicables' ? :canal OR "
                "(metadata::jsonb)->'canales_aplicables' ? 'todos')"
            )
            params["canal"] = canal

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT id, text, metadata,
                   1 - (embedding <=> CAST(:q AS vector)) AS score
            FROM kb_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> CAST(:q AS vector)
            LIMIT :k;
        """
        rows = self.db.execute(sql_text(sql), params).fetchall()

        return [
            {
                "id": r[0],
                "text": r[1],
                "metadata": r[2],
                "score": float(r[3]),
                "citation": (r[2] or {}).get("citation", ""),
            }
            for r in rows
        ]


def format_context(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(sin fuentes recuperadas)"
    parts = []
    for i, c in enumerate(chunks, 1):
        cit = c.get("citation", "sin cita")
        parts.append(f"[Fuente {i}] {c['text']}\n-> Citar como: {cit}")
    return "\n\n".join(parts)
