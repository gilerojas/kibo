from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from app.models.schemas import TelegramMessage


class TelegramClient:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"

    def get_updates(self, *, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        response = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=timeout + 5)
        response.raise_for_status()
        return response.json().get("result", [])

    def send_message(self, chat_id: int, text: str) -> None:
        response = requests.post(
            f"{self.base_url}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
        response.raise_for_status()


def telegram_message_from_update(update: dict[str, Any], *, tz) -> TelegramMessage | None:
    message = update.get("message") or {}
    text = message.get("text")
    from_user = message.get("from") or {}
    chat = message.get("chat") or {}
    if not text or not from_user.get("id") or not chat.get("id"):
        return None
    return TelegramMessage(
        update_id=int(update["update_id"]),
        message_id=int(message["message_id"]),
        chat_id=int(chat["id"]),
        user_id=int(from_user["id"]),
        text=str(text),
        received_at=datetime.fromtimestamp(int(message.get("date", 0)), tz=tz),
    )
