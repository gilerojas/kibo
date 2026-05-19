from datetime import datetime

from app.models.schemas import Intent
from app.services.parser import parse_command


def test_parse_note() -> None:
    parsed = parse_command("/note idea for Kibo")
    assert parsed.intent == Intent.NOTE
    assert parsed.body == "idea for Kibo"
    assert parsed.parsed_payload["text"] == "idea for Kibo"


def test_parse_task_with_tomorrow_date() -> None:
    now = datetime(2026, 5, 18, 12, 0)
    parsed = parse_command("/task Call supplier tomorrow", now=now)
    assert parsed.intent == Intent.TASK
    assert parsed.parsed_payload["date"] == "2026-05-19"


def test_parse_link_extracts_url() -> None:
    parsed = parse_command("/link read https://example.com later")
    assert parsed.intent == Intent.LINK
    assert parsed.parsed_payload["url"] == "https://example.com"


def test_parse_reminder_datetime() -> None:
    now = datetime(2026, 5, 18, 12, 0)
    parsed = parse_command("/remind Review invoices Friday at 9am", now=now)
    assert parsed.intent == Intent.REMINDER
    assert parsed.parsed_payload["date"] == "2026-05-22"
    assert parsed.parsed_payload["datetime"] == "2026-05-22T09:00:00"


def test_parse_summary_today() -> None:
    parsed = parse_command("/summary today")
    assert parsed.intent == Intent.SUMMARY
    assert parsed.parsed_payload["period"] == "today"


def test_parse_empty_command_argument() -> None:
    parsed = parse_command("/note")
    assert parsed.intent == Intent.NOTE
    assert parsed.error == "/note needs text after the command."


def test_parse_unknown() -> None:
    parsed = parse_command("hello")
    assert parsed.intent == Intent.UNKNOWN
    assert parsed.error == "Unknown command. Try /help."
