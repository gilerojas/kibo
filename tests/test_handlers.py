from datetime import datetime
from uuid import uuid4

from app.config import Settings
from app.models.schemas import ActionResult, TelegramMessage
from app.services.handlers import KiboHandler


class FakeRepository:
    def __init__(self) -> None:
        self.actions = []
        self.statuses = []
        self.command_id = uuid4()
        self.user_id = uuid4()

    def upsert_user(self, message, *, timezone):
        return self.user_id

    def create_command(self, **kwargs):
        return self.command_id

    def update_command_status(self, command_id, status, *, error_message=None):
        self.statuses.append((command_id, status, error_message))

    def create_action(self, *, command_id, user_id, result):
        self.actions.append(result)
        return uuid4()

    def summary_for_day(self, user_id, day):
        return {"date": day.isoformat(), "counts": [{"intent": "note", "status": "processed", "count": 1}]}


class FakeNotion:
    def __init__(self) -> None:
        self.created = []

    def create_for_intent(self, intent, payload, raw_text):
        self.created.append((intent, payload, raw_text))
        return ActionResult("notion", intent.value, "succeeded", external_id="abc", external_url="https://notion.so/abc")

    def create_log(self, title, content):
        return ActionResult("notion", "summary_log", "succeeded", external_id="log")


def make_message(text: str, user_id: int = 123) -> TelegramMessage:
    return TelegramMessage(
        update_id=1,
        message_id=10,
        chat_id=20,
        user_id=user_id,
        text=text,
        received_at=datetime(2026, 5, 18, 12, 0),
    )


def test_handler_creates_note() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/note test note"))

    assert response.startswith("Saved note: test note")
    assert notion.created[0][0].value == "note"
    assert repo.actions[0].status == "succeeded"


def test_handler_rejects_unauthorized_user() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/note test", user_id=999))

    assert "not authorized" in response
    assert not notion.created
    assert repo.actions[0].status == "rejected"


def test_handler_summary() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/summary today"))

    assert "Kibo Summary" in response
    assert "note / processed: 1" in response
