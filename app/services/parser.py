from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.models.schemas import Intent, ParsedCommand

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
AMPM_TIME_RE = re.compile(r"\b(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)\b", re.IGNORECASE)
AT_TIME_RE = re.compile(r"\bat\s+(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))\b", re.IGNORECASE)
TIME_RANGE_RE = re.compile(
    r"\bfrom\s+(?P<start_hour>\d{1,2})(?::(?P<start_minute>\d{2}))?\s*(?P<start_ampm>am|pm)?\s+to\s+(?P<end_hour>\d{1,2})(?::(?P<end_minute>\d{2}))?\s*(?P<end_ampm>am|pm)?\b",
    re.IGNORECASE,
)
SCHEDULE_PREFIX_RE = re.compile(r"^\s*(?:ok\s+)?(?:kibo\s+)?(?:please\s+)?(?:schedule|add|create|put|book)\s+", re.IGNORECASE)
DATE_TIME_TRAILER_RE = re.compile(
    r"\s+\b(?:today|tomorrow|next\s+\w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*$|\s+\bfrom\b.*$|\s+\bat\b.*$",
    re.IGNORECASE,
)
TASK_VERB_RE = re.compile(
    r"^(call|pay|send|review|check|buy|email|message|follow up|follow-up|prepare|finish|submit|renew)\b",
    re.IGNORECASE,
)
EVENT_RE = re.compile(r"\b(schedule|meeting|meet|call with|appointment|event)\b", re.IGNORECASE)
REMINDER_RE = re.compile(r"\b(remind me|reminder|remember to)\b", re.IGNORECASE)
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
    "/start": Intent.START,
    "/note": Intent.NOTE,
    "/task": Intent.TASK,
    "/link": Intent.LINK,
    "/book": Intent.BOOK,
    "/remind": Intent.REMINDER,
    "/event": Intent.EVENT,
    "/summary": Intent.SUMMARY,
    "/today": Intent.TODAY,
    "/week": Intent.WEEK,
    "/search": Intent.SEARCH,
    "/open": Intent.OPEN,
    "/done": Intent.DONE,
    "/help": Intent.HELP,
}


HELP_TEXT = """Kibo commands:
/note <text>
/task <text>
/link <url or text>
/book <title or recommendation>
/remind <text>
/event <text>
/today
/week
/search <query>
/open <query>
/done <query>
/summary today
/help"""

START_TEXT = """Kibo is ready.

Use these commands:
/note <text>
/task <text>
/link <url or text>
/book <title or recommendation>
/remind <text>
/event <text>
/today
/week
/search <query>
/open <query>
/done <query>
/summary today"""


def parse_command(text: str, *, now: datetime | None = None) -> ParsedCommand:
    raw_text = text.strip()
    if not raw_text:
        return ParsedCommand(Intent.UNKNOWN, text, error="Send a Kibo command. Try /help.")

    command, _, body = raw_text.partition(" ")
    command = command.lower()
    body = body.strip()
    intent = COMMANDS.get(command)
    if intent is None:
        return parse_natural_command(raw_text, now=now)

    if intent in {Intent.START, Intent.HELP, Intent.TODAY, Intent.WEEK}:
        return ParsedCommand(intent, text, body=body)

    if intent in {Intent.SEARCH, Intent.OPEN, Intent.DONE}:
        if not body:
            return ParsedCommand(intent, text, error=f"{command} needs search text after the command.")
        return ParsedCommand(intent, text, body=body, parsed_payload={"query": body})

    if intent == Intent.SUMMARY:
        period = body.lower() or "today"
        if period != "today":
            return ParsedCommand(intent, text, body=body, error="Only /summary today is supported in this MVP.")
        return ParsedCommand(intent, text, body=body, parsed_payload={"period": "today"})

    if not body:
        return ParsedCommand(intent, text, error=f"{command} needs text after the command.")

    payload: dict[str, object] = {"text": body}
    if intent in {Intent.LINK, Intent.BOOK}:
        match = URL_RE.search(body)
        if match:
            payload["url"] = match.group(0)
    if intent in {Intent.REMINDER, Intent.EVENT, Intent.TASK}:
        payload.update(extract_simple_schedule(body, now=now))

    return ParsedCommand(intent, text, body=body, parsed_payload=payload)


def parse_natural_command(raw_text: str, *, now: datetime | None = None) -> ParsedCommand:
    lower = raw_text.lower().strip()
    schedule = extract_simple_schedule(raw_text, now=now)

    if URL_RE.search(raw_text):
        payload: dict[str, object] = {"text": raw_text, "url": URL_RE.search(raw_text).group(0)}
        return ParsedCommand(Intent.LINK, raw_text, body=raw_text, parsed_payload=payload)

    if lower.startswith(("idea:", "idea ")):
        body = raw_text.split(":", 1)[1].strip() if ":" in raw_text else raw_text[5:].strip()
        return ParsedCommand(Intent.NOTE, raw_text, body=body, parsed_payload={"text": body})

    if lower.startswith(("note:", "nota:")):
        body = raw_text.split(":", 1)[1].strip()
        return ParsedCommand(Intent.NOTE, raw_text, body=body, parsed_payload={"text": body})

    if lower.startswith(("book:", "libro:")):
        body = raw_text.split(":", 1)[1].strip()
        payload = {"text": body}
        match = URL_RE.search(body)
        if match:
            payload["url"] = match.group(0)
        return ParsedCommand(Intent.BOOK, raw_text, body=body, parsed_payload=payload)

    if REMINDER_RE.search(lower):
        body = clean_reminder_text(raw_text)
        payload = {"text": body, **schedule}
        if "datetime" not in payload and "date" not in payload:
            return ParsedCommand(
                Intent.UNKNOWN,
                raw_text,
                body=raw_text,
                error="I can create a reminder, but I need a date or time. Try: remind me tomorrow at 9am to review invoices.",
                needs_clarification=True,
            )
        return ParsedCommand(Intent.REMINDER, raw_text, body=body, parsed_payload=payload)

    if EVENT_RE.search(lower) and schedule:
        body = clean_event_text(raw_text)
        return ParsedCommand(Intent.EVENT, raw_text, body=body, parsed_payload={"text": body, **schedule})

    if TASK_VERB_RE.search(lower):
        return ParsedCommand(Intent.TASK, raw_text, body=raw_text, parsed_payload={"text": raw_text, **schedule})

    return ParsedCommand(
        Intent.UNKNOWN,
        raw_text,
        body=raw_text,
        error="I am not sure whether this is a note, task, link, reminder, or event. Use /note, /task, /link, /remind, or /event.",
        needs_clarification=True,
    )


def clean_reminder_text(text: str) -> str:
    cleaned = re.sub(r"^\s*remind me\s+", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*remember to\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*reminder[:\s]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bto\s+", "", cleaned, count=1, flags=re.IGNORECASE)
    return cleaned.strip() or text.strip()


def clean_event_text(text: str) -> str:
    cleaned = SCHEDULE_PREFIX_RE.sub("", text.strip())
    cleaned = DATE_TIME_TRAILER_RE.sub("", cleaned).strip()
    return cleaned or text.strip()


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
    range_match = TIME_RANGE_RE.search(lower)
    time_match = range_match or AMPM_TIME_RE.search(lower) or AT_TIME_RE.search(lower)
    if date_value is None and time_match is not None:
        date_value = now.date()

    if date_value is not None:
        result["date"] = date_value.isoformat()

    if range_match and date_value is not None:
        start_hour, start_minute = normalize_hour(
            int(range_match.group("start_hour")),
            int(range_match.group("start_minute") or "0"),
            range_match.group("start_ampm") or range_match.group("end_ampm"),
        )
        end_hour, end_minute = normalize_hour(
            int(range_match.group("end_hour")),
            int(range_match.group("end_minute") or "0"),
            range_match.group("end_ampm") or range_match.group("start_ampm"),
        )
        if not range_match.group("start_ampm") and not range_match.group("end_ampm"):
            end_hour, end_minute = infer_end_hour_for_bare_range(start_hour, start_minute, end_hour, end_minute)
        if 0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_hour <= 23 and 0 <= end_minute <= 59:
            result["datetime"] = datetime.combine(date_value, datetime.min.time(), tzinfo=now.tzinfo).replace(
                hour=start_hour,
                minute=start_minute,
            ).isoformat()
            result["end_datetime"] = datetime.combine(date_value, datetime.min.time(), tzinfo=now.tzinfo).replace(
                hour=end_hour,
                minute=end_minute,
            ).isoformat()
        return result

    if time_match and date_value is not None:
        hour = int(time_match.group("hour"))
        minute = int(time_match.group("minute") or "0")
        ampm = time_match.groupdict().get("ampm")
        hour, minute = normalize_hour(hour, minute, ampm)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            result["datetime"] = datetime.combine(date_value, datetime.min.time(), tzinfo=now.tzinfo).replace(
                hour=hour,
                minute=minute,
            ).isoformat()

    return result


def normalize_hour(hour: int, minute: int, ampm: str | None) -> tuple[int, int]:
    if ampm:
        if ampm.lower() == "pm" and hour < 12:
            hour += 12
        if ampm.lower() == "am" and hour == 12:
            hour = 0
    return hour, minute


def infer_end_hour_for_bare_range(start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> tuple[int, int]:
    if (end_hour, end_minute) > (start_hour, start_minute):
        return end_hour, end_minute
    if end_hour < 12:
        return end_hour + 12, end_minute
    return end_hour, end_minute
