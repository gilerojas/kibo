from datetime import datetime
from uuid import uuid4

from app.config import Settings
from app.models.schemas import ActionResult, TelegramMessage
from app.services.handlers import KiboHandler


class FakeRepository:
    def __init__(self) -> None:
        self.actions = []
        self.statuses = []
        self.reminders = []
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

    def today_items(self, user_id, day):
        return {
            "date": day.isoformat(),
            "items": [
                {
                    "intent": "task",
                    "raw_text": "/task Call supplier today",
                    "parsed_payload": {"date": day.isoformat()},
                    "external_url": "https://notion.so/task",
                }
            ],
        }

    def upcoming_items(self, user_id, start_day, end_day):
        return {
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
            "items": [
                {
                    "intent": "event",
                    "raw_text": "schedule gym from 6 to 7 pm",
                    "parsed_payload": {"datetime": f"{start_day.isoformat()}T18:00:00"},
                    "external_url": "https://notion.so/event",
                }
            ],
        }

    def search_items(self, user_id, query):
        if query == "missing":
            return []
        return [
            {
                "command_id": self.command_id,
                "intent": "task",
                "raw_text": "/task Call supplier tomorrow",
                "parsed_payload": {"text": "Call supplier tomorrow"},
                "external_id": "page-id",
                "external_url": "https://notion.so/task",
            }
        ]

    def best_open_item(self, user_id, query):
        rows = self.search_items(user_id, query)
        return rows[0] if rows else None

    def best_completable_item(self, user_id, query):
        rows = self.search_items(user_id, query)
        return rows[0] if rows else None

    def mark_reminder_done_for_command(self, command_id):
        self.reminders.append({"done_command_id": command_id})

    def create_reminder(self, **kwargs):
        self.reminders.append(kwargs)
        return uuid4()


class FakeNotion:
    def __init__(self) -> None:
        self.created = []
        self.done = []

    def create_for_intent(self, intent, payload, raw_text):
        self.created.append((intent, payload, raw_text))
        return ActionResult("notion", intent.value, "succeeded", external_id="abc", external_url="https://notion.so/abc")

    def create_log(self, title, content):
        return ActionResult("notion", "summary_log", "succeeded", external_id="log")

    def mark_done(self, page_id, intent):
        self.done.append((page_id, intent))
        return ActionResult("notion", "done", "succeeded", external_id=page_id, external_url="https://notion.so/done")


class FakeLlmParser:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, text, *, now):
        self.calls.append((text, now))
        return self.parsed


def make_message(text: str, user_id: int = 123, chat_type: str = "private") -> TelegramMessage:
    return TelegramMessage(
        update_id=1,
        message_id=10,
        chat_id=20,
        user_id=user_id,
        text=text,
        received_at=datetime(2026, 5, 18, 12, 0),
        chat_type=chat_type,
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
    assert "Today:" in response


def test_handler_today() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/today"))

    assert "Today" in response
    assert "/task Call supplier today" in response
    assert not notion.created


def test_handler_creates_scheduled_reminder() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/remind Review invoices today at 9am"))

    assert response.startswith("Created reminder")
    assert len(repo.reminders) == 1
    assert repo.reminders[0]["title"] == "Review invoices today at 9am"


def test_handler_start_returns_onboarding() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/start"))

    assert "Kibo is ready" in response
    assert "/note <text>" in response
    assert not notion.created


def test_handler_rejects_group_chat() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/note team note", chat_type="group"))

    assert "private chat" in response
    assert not notion.created


def test_handler_creates_natural_task() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("pay edenorte tomorrow"))

    assert response.startswith("Created task")
    assert notion.created[0][0].value == "task"


def test_handler_clarifies_ambiguous_natural_message() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("just thinking out loud"))

    assert "Use /note" in response
    assert not notion.created


def test_handler_uses_llm_for_ambiguous_natural_message() -> None:
    from app.models.schemas import Intent, ParsedCommand

    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    llm = FakeLlmParser(
        ParsedCommand(
            Intent.TASK,
            "tengo que llamar a Elayne el viernes",
            body="Llamar a Elayne",
            parsed_payload={"text": "Llamar a Elayne", "date": "2026-05-22", "llm": {"confidence": 0.93}},
        )
    )
    handler = KiboHandler(settings, repo, notion, llm_parser=llm)

    response = handler.handle(make_message("tengo que llamar a Elayne el viernes"))

    assert response.startswith("Created task")
    assert llm.calls
    assert notion.created[0][0].value == "task"


def test_handler_does_not_call_llm_for_slash_command() -> None:
    from app.models.schemas import Intent, ParsedCommand

    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    llm = FakeLlmParser(ParsedCommand(Intent.TASK, "unused", body="unused", parsed_payload={"text": "unused"}))
    handler = KiboHandler(settings, repo, notion, llm_parser=llm)

    response = handler.handle(make_message("/note deterministic"))

    assert response.startswith("Saved note")
    assert not llm.calls


def test_handler_schedules_time_range_as_event() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("schedule gym from 6 to 7 pm"))

    assert response.startswith("Created event")
    assert notion.created[0][0].value == "event"
    assert "end_datetime" in notion.created[0][1]


def test_handler_week() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/week"))

    assert "Week" in response
    assert "schedule gym" in response


def test_handler_search() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/search supplier"))

    assert "Search results" in response
    assert "Call supplier tomorrow" in response


def test_handler_open() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/open supplier"))

    assert "Call supplier tomorrow" in response
    assert "https://notion.so/task" in response


def test_handler_done_marks_notion_done() -> None:
    repo = FakeRepository()
    notion = FakeNotion()
    settings = Settings(telegram_allowed_user_ids="123")
    handler = KiboHandler(settings, repo, notion)

    response = handler.handle(make_message("/done supplier"))

    assert "Marked done" in response
    assert notion.done[0][0] == "page-id"
    assert repo.actions[-1].action_type == "done"
