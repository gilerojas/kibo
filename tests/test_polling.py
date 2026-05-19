from datetime import datetime
from uuid import uuid4

from app.bot.polling import send_due_reminders


class FakeRepository:
    def __init__(self) -> None:
        self.reminder_id = uuid4()
        self.sent = []
        self.failed = []

    def due_reminders(self, now, *, limit):
        return [
            {
                "id": self.reminder_id,
                "telegram_chat_id": 123,
                "title": "Review invoices",
                "reminder_at": now,
                "notion_url": "https://notion.so/reminder",
            }
        ]

    def mark_reminder_sent(self, reminder_id):
        self.sent.append(reminder_id)

    def mark_reminder_failed(self, reminder_id, error_message):
        self.failed.append((reminder_id, error_message))


class FakeTelegram:
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


class FakeSettings:
    tzinfo = datetime.now().astimezone().tzinfo


def test_send_due_reminders_marks_sent() -> None:
    repo = FakeRepository()
    telegram = FakeTelegram()

    send_due_reminders(repo, telegram, FakeSettings())

    assert telegram.messages == [(123, "Reminder: Review invoices\nhttps://notion.so/reminder")]
    assert repo.sent == [repo.reminder_id]
    assert repo.failed == []
