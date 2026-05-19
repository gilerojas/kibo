from datetime import datetime

from app.models.schemas import Intent
from app.services.parser import parse_command


def test_parse_note() -> None:
    parsed = parse_command("/note idea for Kibo")
    assert parsed.intent == Intent.NOTE
    assert parsed.body == "idea for Kibo"
    assert parsed.parsed_payload["text"] == "idea for Kibo"


def test_parse_start() -> None:
    parsed = parse_command("/start")
    assert parsed.intent == Intent.START
    assert not parsed.error


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


def test_parse_reminder_ignores_unrelated_numbers() -> None:
    now = datetime(2026, 5, 19, 12, 0)
    parsed = parse_command("/remind Phase 1 reminder smoke test tomorrow at 9am", now=now)
    assert parsed.intent == Intent.REMINDER
    assert parsed.parsed_payload["datetime"] == "2026-05-20T09:00:00"


def test_parse_summary_today() -> None:
    parsed = parse_command("/summary today")
    assert parsed.intent == Intent.SUMMARY
    assert parsed.parsed_payload["period"] == "today"


def test_parse_today() -> None:
    parsed = parse_command("/today")
    assert parsed.intent == Intent.TODAY
    assert not parsed.error


def test_parse_week() -> None:
    parsed = parse_command("/week")
    assert parsed.intent == Intent.WEEK
    assert not parsed.error


def test_parse_search_open_done() -> None:
    assert parse_command("/search invoices").intent == Intent.SEARCH
    assert parse_command("/open invoices").intent == Intent.OPEN
    assert parse_command("/done invoices").intent == Intent.DONE


def test_parse_search_requires_query() -> None:
    parsed = parse_command("/search")
    assert parsed.intent == Intent.SEARCH
    assert parsed.error == "/search needs search text after the command."


def test_parse_empty_command_argument() -> None:
    parsed = parse_command("/note")
    assert parsed.intent == Intent.NOTE
    assert parsed.error == "/note needs text after the command."


def test_parse_unknown() -> None:
    parsed = parse_command("hello")
    assert parsed.intent == Intent.UNKNOWN
    assert parsed.needs_clarification


def test_parse_natural_task() -> None:
    now = datetime(2026, 5, 18, 12, 0)
    parsed = parse_command("pay edenorte tomorrow", now=now)
    assert parsed.intent == Intent.TASK
    assert parsed.body == "pay edenorte tomorrow"
    assert parsed.parsed_payload["date"] == "2026-05-19"


def test_parse_natural_link() -> None:
    parsed = parse_command("save https://example.com for later")
    assert parsed.intent == Intent.LINK
    assert parsed.parsed_payload["url"] == "https://example.com"


def test_parse_natural_idea_note() -> None:
    parsed = parse_command("idea: greq pricing dashboard")
    assert parsed.intent == Intent.NOTE
    assert parsed.body == "greq pricing dashboard"


def test_parse_natural_reminder() -> None:
    now = datetime(2026, 5, 18, 12, 0)
    parsed = parse_command("remind me tomorrow at 9am to review invoices", now=now)
    assert parsed.intent == Intent.REMINDER
    assert parsed.parsed_payload["datetime"] == "2026-05-19T09:00:00"


def test_parse_natural_event() -> None:
    now = datetime(2026, 5, 18, 12, 0)
    parsed = parse_command("meeting with Richard tomorrow at 5pm", now=now)
    assert parsed.intent == Intent.EVENT
    assert parsed.parsed_payload["datetime"] == "2026-05-19T17:00:00"


def test_parse_schedule_time_range_as_event_today() -> None:
    now = datetime(2026, 5, 19, 12, 0)
    parsed = parse_command("schedule gym from 6 to 7 pm", now=now)
    assert parsed.intent == Intent.EVENT
    assert parsed.parsed_payload["date"] == "2026-05-19"
    assert parsed.parsed_payload["datetime"] == "2026-05-19T18:00:00"
    assert parsed.parsed_payload["end_datetime"] == "2026-05-19T19:00:00"


def test_parse_natural_ambiguous_text_clarifies() -> None:
    parsed = parse_command("random thought with no signal")
    assert parsed.intent == Intent.UNKNOWN
    assert parsed.needs_clarification
    assert "not sure" in parsed.error
