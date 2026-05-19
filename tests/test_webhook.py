from datetime import datetime

from fastapi.testclient import TestClient

import app.routers.telegram as telegram_router
from app.config import get_settings
from app.main import app


class FakeTelegram:
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


class FakeHandler:
    def __init__(self) -> None:
        self.messages = []

    def handle(self, message):
        self.messages.append(message)
        return "handled"


def test_webhook_rejects_bad_secret(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "telegram_webhook_secret", "secret")

    client = TestClient(app)
    response = client.post("/telegram/webhook", json={"update_id": 1})

    assert response.status_code == 401


def test_webhook_handles_message(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "telegram_webhook_secret", "secret")
    fake_telegram = FakeTelegram()
    fake_handler = FakeHandler()
    monkeypatch.setattr(telegram_router, "get_runtime", lambda: (fake_telegram, fake_handler))

    client = TestClient(app)
    response = client.post(
        "/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "secret"},
        json={
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": int(datetime(2026, 5, 19).timestamp()),
                "text": "/today",
                "from": {"id": 123},
                "chat": {"id": 456, "type": "private"},
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert fake_handler.messages[0].text == "/today"
    assert fake_telegram.messages == [(456, "handled")]
