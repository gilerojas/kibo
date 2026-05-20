from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import requests

from app.config import Settings
from app.models.schemas import Intent, ParsedCommand

ALLOWED_INTENTS = {
    Intent.NOTE.value,
    Intent.TASK.value,
    Intent.LINK.value,
    Intent.BOOK.value,
    Intent.REMINDER.value,
    Intent.EVENT.value,
    Intent.UNKNOWN.value,
}


class AnthropicParser:
    def __init__(self, settings: Settings):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.timezone = settings.default_timezone

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def parse(self, text: str, *, now: datetime) -> ParsedCommand:
        if not self.is_configured:
            return clarification(text, "LLM parser is not configured. Use /note, /task, /link, /book, /remind, or /event.")

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 500,
                "temperature": 0,
                "system": system_prompt(self.timezone, now),
                "messages": [{"role": "user", "content": text}],
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        content = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        return parsed_command_from_llm_json(text, content, model=self.model)


def system_prompt(timezone: str, now: datetime) -> str:
    return f"""You classify one Telegram productivity message for Kibo.

Return only valid JSON. No markdown.

Current datetime: {now.isoformat()}
Timezone: {timezone}

Allowed intents:
- note
- task
- link
- book
- reminder
- event
- unknown

Schema:
{{
  "intent": "task",
  "confidence": 0.0,
  "title": "short cleaned title",
  "items": [
    {{
      "title": "single cleaned item title",
      "date": "YYYY-MM-DD or null",
      "datetime": "ISO-8601 datetime or null",
      "url": "https://... or null"
    }}
  ],
  "date": "YYYY-MM-DD or null",
  "datetime": "ISO-8601 datetime or null",
  "url": "https://... or null",
  "needs_clarification": false,
  "clarification_question": null
}}

Rules:
- Use link when the message contains a URL and is mainly for saving/reading later.
- Use book when the message is a book recommendation, reading list item, or book to remember.
- Use reminder only when the user wants Kibo to remind them. A reminder needs a date or datetime.
- Use event for meetings, appointments, calls, or scheduled blocks with a date/time.
- Use task for action items the user needs to do.
- Use note for ideas, observations, or information to save.
- Use unknown if the message is too vague.
- If the message contains a bullet list or numbered list of multiple tasks, notes, links, books, reminders, or events with the same intent, return each entry in items.
- Apply shared date/datetime context to all items when a phrase like tomorrow or Friday introduces the list.
- If there is only one item, items can be null or omitted.
- Convert relative dates like tomorrow, Friday, next Monday using the current datetime.
- If exact time is present, include datetime. If only date is present, include date.
- Confidence must reflect ambiguity. Do not exceed 0.79 if clarification is needed.
"""


def parsed_command_from_llm_json(raw_text: str, content: str, *, model: str) -> ParsedCommand:
    try:
        payload = json.loads(extract_json_object(content))
    except json.JSONDecodeError:
        return clarification(raw_text, "I could not parse that reliably. Use /note, /task, /link, /book, /remind, or /event.")

    intent_value = str(payload.get("intent", "unknown")).lower()
    if intent_value not in ALLOWED_INTENTS:
        intent_value = Intent.UNKNOWN.value

    confidence = float(payload.get("confidence") or 0)
    needs_clarification = bool(payload.get("needs_clarification")) or confidence < 0.8 or intent_value == Intent.UNKNOWN.value
    question = payload.get("clarification_question") or "I am not sure what to do with this. Should it be a note, task, link, book, reminder, or event?"

    body = str(payload.get("title") or raw_text).strip()
    parsed_payload: dict[str, Any] = {
        "text": body,
        "llm": {
            "provider": "anthropic",
            "model": model,
            "confidence": confidence,
        },
    }
    for key in ("date", "datetime", "url"):
        value = payload.get(key)
        if value:
            parsed_payload[key] = value
    items = clean_llm_items(payload.get("items"))
    if items:
        parsed_payload["items"] = items

    if needs_clarification:
        return ParsedCommand(
            Intent.UNKNOWN,
            raw_text,
            body=raw_text,
            parsed_payload=parsed_payload,
            error=str(question),
            needs_clarification=True,
        )

    return ParsedCommand(Intent(intent_value), raw_text, body=body, parsed_payload=parsed_payload)


def clean_llm_items(items: Any) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []

    cleaned: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("text") or "").strip()
        if not title:
            continue
        cleaned_item = {"text": title}
        for key in ("date", "datetime", "url"):
            value = item.get(key)
            if value:
                cleaned_item[key] = str(value)
        cleaned.append(cleaned_item)
    return cleaned


def clarification(raw_text: str, message: str) -> ParsedCommand:
    return ParsedCommand(Intent.UNKNOWN, raw_text, body=raw_text, error=message, needs_clarification=True)


def extract_json_object(content: str) -> str:
    stripped = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]
    return stripped
