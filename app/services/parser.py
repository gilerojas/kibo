from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.models.schemas import Intent, ParsedCommand

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
TIME_RE = re.compile(r"\b(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?\b", re.IGNORECASE)
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


COMMANDS = {
    "/note": Intent.NOTE,
    "/task": Intent.TASK,
    "/link": Intent.LINK,
    "/remind": Intent.REMINDER,
    "/event": Intent.EVENT,
    "/summary": Intent.SUMMARY,
    "/help": Intent.HELP,
}


HELP_TEXT = """Kibo commands:
/note <text>
/task <text>
/link <url or text>
/remind <text>
/event <text>
/summary today
/help"""


def parse_command(text: str, *, now: datetime | None = None) -> ParsedCommand:
    raw_text = text.strip()
    if not raw_text:
        return ParsedCommand(Intent.UNKNOWN, text, error="Send a Kibo command. Try /help.")

    command, _, body = raw_text.partition(" ")
    command = command.lower()
    body = body.strip()
    intent = COMMANDS.get(command)
    if intent is None:
        return ParsedCommand(Intent.UNKNOWN, text, body=raw_text, error="Unknown command. Try /help.")

    if intent == Intent.HELP:
        return ParsedCommand(intent, text, body=body)

    if intent == Intent.SUMMARY:
        period = body.lower() or "today"
        if period != "today":
            return ParsedCommand(intent, text, body=body, error="Only /summary today is supported in this MVP.")
        return ParsedCommand(intent, text, body=body, parsed_payload={"period": "today"})

    if not body:
        return ParsedCommand(intent, text, error=f"{command} needs text after the command.")

    payload: dict[str, object] = {"text": body}
    if intent == Intent.LINK:
        match = URL_RE.search(body)
        if match:
            payload["url"] = match.group(0)
    if intent in {Intent.REMINDER, Intent.EVENT, Intent.TASK}:
        payload.update(extract_simple_schedule(body, now=now))

    return ParsedCommand(intent, text, body=body, parsed_payload=payload)


def extract_simple_schedule(text: str, *, now: datetime | None = None) -> dict[str, object]:
    now = now or datetime.now()
    lower = text.lower()
    date_value = None

    if "today" in lower:
        date_value = now.date()
    elif "tomorrow" in lower:
        date_value = (now + timedelta(days=1)).date()
    else:
        for name, target_weekday in WEEKDAYS.items():
            if name in lower:
                days_ahead = (target_weekday - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                date_value = (now + timedelta(days=days_ahead)).date()
                break

    result: dict[str, object] = {}
    if date_value is not None:
        result["date"] = date_value.isoformat()

    time_match = TIME_RE.search(lower)
    if time_match and date_value is not None:
        hour = int(time_match.group("hour"))
        minute = int(time_match.group("minute") or "0")
        ampm = time_match.group("ampm")
        if ampm:
            if ampm.lower() == "pm" and hour < 12:
                hour += 12
            if ampm.lower() == "am" and hour == 12:
                hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            result["datetime"] = datetime.combine(date_value, datetime.min.time()).replace(
                hour=hour,
                minute=minute,
            ).isoformat()

    return result
