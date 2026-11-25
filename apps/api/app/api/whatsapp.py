"""Webhook de WhatsApp Business Platform (stub listo para integración)."""
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.chat import post_message
from app.config import get_settings
from app.db import get_db
from app.models.schemas import ChatRequest

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
log = logging.getLogger(__name__)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
):
    """Verificación inicial del webhook (Meta exige responder con el challenge)."""
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
    return {"status": "verification_failed"}


@router.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    """
    Recibe mensajes entrantes de WhatsApp.
    STUB: parsea el payload, lo transforma en ChatRequest y lo pasa al mismo orquestador.
    En producción: también debe enviar la respuesta de vuelta vía Graph API.
    """
    body = await request.json()
    log.info(f"WhatsApp webhook payload: {body}")

    # Payload típico de Meta: entry[].changes[].value.messages[]
    try:
        value = body["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ignored", "reason": "no messages"}
        msg = value["messages"][0]
        from_phone = msg["from"]
        text = msg.get("text", {}).get("body", "")
    except (KeyError, IndexError) as e:
        log.warning(f"Payload de WhatsApp no reconocido: {e}")
        return {"status": "ignored", "reason": "invalid payload"}

    # Mapear teléfono → session (stub simple: una sesión por teléfono)
    session_id = f"whatsapp-{from_phone}"
    req = ChatRequest(session_id=None, channel="whatsapp", message=text)
    # TODO: lookup real por teléfono y enviar respuesta vía Graph API
    response = post_message(req, db=db)
    return {"status": "processed", "session_id": response.session_id, "reply": response.reply[:200]}
