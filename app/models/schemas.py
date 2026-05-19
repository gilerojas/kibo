from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Intent(StrEnum):
    START = "start"
    NOTE = "note"
    TASK = "task"
    LINK = "link"
    REMINDER = "reminder"
    EVENT = "event"
    SUMMARY = "summary"
    TODAY = "today"
    WEEK = "week"
    SEARCH = "search"
    OPEN = "open"
    DONE = "done"
    HELP = "help"
    UNKNOWN = "unknown"


class CommandStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ParsedCommand:
    intent: Intent
    raw_text: str
    body: str = ""
    parsed_payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    needs_clarification: bool = False


@dataclass(frozen=True)
class TelegramMessage:
    update_id: int
    message_id: int
    chat_id: int
    user_id: int
    text: str
    received_at: datetime
    chat_type: str = "private"


@dataclass(frozen=True)
class ActionResult:
    destination: str
    action_type: str
    status: str
    external_id: str | None = None
    external_url: str | None = None
    error_message: str | None = None
