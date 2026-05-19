from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from app.bot.telegram_client import telegram_message_from_update
from app.config import get_settings
from app.runtime import get_runtime

logger = logging.getLogger("kibo.telegram.webhook")

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
def telegram_webhook(
    update: dict[str, Any],
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    telegram, handler = get_runtime()
    message = telegram_message_from_update(update, tz=settings.tzinfo)
    if message is None:
        return {"ok": True}

    try:
        response_text = handler.handle(message)
    except Exception:
        logger.exception("Failed to process Telegram webhook update %s", update.get("update_id"))
        response_text = "Kibo hit an internal error while processing this command."

    telegram.send_message(message.chat_id, response_text)
    return {"ok": True}
