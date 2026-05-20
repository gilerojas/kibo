from __future__ import annotations

from datetime import datetime, timedelta

from app.config import Settings
from app.models.schemas import ActionResult, CommandStatus, Intent, ParsedCommand, TelegramMessage
from app.services.auth import is_authorized_user
from app.services.llm_parser import AnthropicParser
from app.services.parser import HELP_TEXT, START_TEXT, parse_command


class KiboHandler:
    def __init__(
        self,
        settings: Settings,
        repository,
        notion,
        llm_parser=None,
    ):
        self.settings = settings
        self.repository = repository
        self.notion = notion
        self.llm_parser = llm_parser or AnthropicParser(settings)

    def handle(self, message: TelegramMessage) -> str:
        now = datetime.now(self.settings.tzinfo)
        parsed = self._parse_message(message.text, now=now)

        if not is_authorized_user(message.user_id, self.settings):
            command_id = self.repository.create_command(
                user_id=None,
                message=message,
                parsed=parsed,
                status=CommandStatus.REJECTED,
                error_message="Unauthorized Telegram user",
            )
            self.repository.create_action(
                command_id=command_id,
                user_id=None,
                result=ActionResult("telegram", "authorize", "rejected", error_message="Unauthorized Telegram user"),
            )
            return "Kibo is not authorized for this Telegram user."

        user_id = self.repository.upsert_user(message, timezone=self.settings.default_timezone)

        if message.chat_type != "private":
            command_id = self.repository.create_command(user_id=user_id, message=message, parsed=parsed)
            self.repository.update_command_status(
                command_id,
                CommandStatus.REJECTED,
                error_message="Kibo MVP only supports private Telegram chats",
            )
            return "Kibo currently works only in a private chat. Open this bot directly and send /start."

        if parsed.needs_clarification and not message.text.strip().startswith("/"):
            clarified = self._resolve_pending_clarification(user_id, message.text, now=now)
            if clarified and not clarified.needs_clarification:
                parsed = clarified

        command_id = self.repository.create_command(user_id=user_id, message=message, parsed=parsed)

        if parsed.error:
            status = CommandStatus.REJECTED if parsed.needs_clarification else CommandStatus.FAILED
            self.repository.update_command_status(command_id, status, error_message=parsed.error)
            return parsed.error

        if parsed.intent == Intent.START:
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return START_TEXT

        if parsed.intent == Intent.HELP:
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return HELP_TEXT

        if parsed.intent == Intent.TODAY:
            today = self.repository.today_items(user_id, datetime.now(self.settings.tzinfo).date())
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return format_today(today)

        if parsed.intent == Intent.WEEK:
            start_day = datetime.now(self.settings.tzinfo).date()
            week = self.repository.upcoming_items(user_id, start_day, start_day + timedelta(days=7))
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return format_week(week)

        if parsed.intent == Intent.SEARCH:
            rows = self.repository.search_items(user_id, parsed.body)
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return format_search_results(parsed.body, rows)

        if parsed.intent == Intent.OPEN:
            row = self.repository.best_open_item(user_id, parsed.body)
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return format_open_result(parsed.body, row)

        if parsed.intent == Intent.DONE:
            row = self.repository.best_completable_item(user_id, parsed.body)
            if not row:
                self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
                return f"I could not find an open task, reminder, or event matching: {parsed.body}"
            if not row.get("external_id"):
                self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message="Matched item has no Notion page ID")
                return "I found a match, but it does not have a Notion page ID to update."
            result = self.notion.mark_done(row["external_id"], Intent(row["intent"]))
            self.repository.create_action(command_id=command_id, user_id=user_id, result=result)
            if result.status == "succeeded":
                self.repository.mark_reminder_done_for_command(row["command_id"])
                self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
                return f"Marked done: {clean_raw_text(row['raw_text'])}\n{result.external_url or row.get('external_url') or ''}".strip()
            self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message=result.error_message)
            return "I found the item, but Notion could not mark it done."

        if parsed.intent == Intent.SUMMARY:
            summary = self.repository.summary_for_day(user_id, datetime.now(self.settings.tzinfo).date())
            today = self.repository.today_items(user_id, datetime.now(self.settings.tzinfo).date())
            response = format_summary(summary, today=today)
            log_result = self.notion.create_log(f"Kibo Summary {summary['date']}", response)
            self.repository.create_action(command_id=command_id, user_id=user_id, result=log_result)
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return response

        if parsed.intent in {Intent.NOTE, Intent.TASK, Intent.LINK, Intent.REMINDER, Intent.EVENT}:
            item_payloads = expanded_item_payloads(parsed.parsed_payload)
            results: list[tuple[dict, ActionResult]] = []
            for payload in item_payloads:
                item_text = str(payload.get("text") or parsed.body)
                result = self.notion.create_for_intent(parsed.intent, payload, item_text)
                self.repository.create_action(command_id=command_id, user_id=user_id, result=result)
                results.append((payload, result))
                if result.status == "succeeded" and parsed.intent == Intent.REMINDER and payload.get("datetime"):
                    reminder_at = datetime.fromisoformat(str(payload["datetime"]))
                    if reminder_at.tzinfo is None:
                        reminder_at = reminder_at.replace(tzinfo=self.settings.tzinfo)
                    self.repository.create_reminder(
                        command_id=command_id,
                        user_id=user_id,
                        telegram_chat_id=message.chat_id,
                        title=item_text,
                        reminder_at=reminder_at,
                        notion_url=result.external_url,
                    )
            failed = [result for _, result in results if result.status != "succeeded"]
            if not failed:
                self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
                if len(results) > 1:
                    return multi_confirmation_for(parsed.intent, results)
                payload, result = results[0]
                return confirmation_for(parsed.intent, str(payload.get("text") or parsed.body), result.external_url)
            self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message=failed[0].error_message)
            return "I saved the command, but Notion could not create the item. Check the Notion integration and database IDs."

        self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message="Unsupported command")
        return "Unsupported command. Try /help."

    def _parse_message(self, text: str, *, now: datetime) -> ParsedCommand:
        parsed = parse_command(text, now=now)
        if parsed.needs_clarification and not text.strip().startswith("/"):
            try:
                return self.llm_parser.parse(text, now=now)
            except Exception:
                return parsed
        return parsed

    def _resolve_pending_clarification(self, user_id, reply_text: str, *, now: datetime) -> ParsedCommand | None:
        if hasattr(self.repository, "recent_pending_clarifications"):
            pending_messages = self.repository.recent_pending_clarifications(user_id, now - timedelta(minutes=30), limit=3)
        elif hasattr(self.repository, "latest_pending_clarification"):
            pending = self.repository.latest_pending_clarification(user_id, now - timedelta(minutes=30))
            pending_messages = [pending] if pending else []
        else:
            return None
        if not pending_messages:
            return None
        pending_context = "\n\n".join(f"- {message['raw_text']}" for message in pending_messages)
        combined = (
            "Previous Kibo messages that needed clarification, oldest first:\n"
            f"{pending_context}\n\n"
            "User clarification reply:\n"
            f"{reply_text}"
        )
        try:
            parsed = self.llm_parser.parse(combined, now=now)
        except Exception:
            return None
        if parsed.needs_clarification:
            return None
        parsed.parsed_payload["clarified_from_command_id"] = str(pending_messages[-1]["id"])
        parsed.parsed_payload["clarified_from_command_ids"] = [str(message["id"]) for message in pending_messages]
        parsed.parsed_payload["clarification_reply"] = reply_text
        return ParsedCommand(
            parsed.intent,
            reply_text,
            body=parsed.body,
            parsed_payload=parsed.parsed_payload,
            error=parsed.error,
            needs_clarification=parsed.needs_clarification,
        )


def confirmation_for(intent: Intent, body: str, url: str | None) -> str:
    prefix = {
        Intent.NOTE: "Saved note",
        Intent.TASK: "Created task",
        Intent.LINK: "Saved link",
        Intent.REMINDER: "Created reminder",
        Intent.EVENT: "Created event",
    }[intent]
    suffix = f"\n{url}" if url else ""
    return f"{prefix}: {body}{suffix}"


def multi_confirmation_for(intent: Intent, results: list[tuple[dict, ActionResult]]) -> str:
    noun = {
        Intent.NOTE: "notes",
        Intent.TASK: "tasks",
        Intent.LINK: "links",
        Intent.REMINDER: "reminders",
        Intent.EVENT: "events",
    }[intent]
    lines = [f"Created {len(results)} {noun}:"]
    for payload, result in results:
        line = f"- {payload.get('text', '').strip()}"
        if result.external_url:
            line += f"\n  {result.external_url}"
        lines.append(line)
    return "\n".join(lines)


def expanded_item_payloads(payload: dict) -> list[dict]:
    items = payload.get("items")
    if not isinstance(items, list) or len(items) < 2:
        return [payload]

    inherited = {key: value for key, value in payload.items() if key not in {"items", "text"}}
    expanded: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("title") or "").strip()
        if not text:
            continue
        item_payload = {**inherited, "text": text}
        for key in ("date", "datetime", "end_datetime", "url"):
            if item.get(key):
                item_payload[key] = item[key]
        expanded.append(item_payload)
    return expanded if len(expanded) > 1 else [payload]


def format_summary(summary: dict, *, today: dict | None = None) -> str:
    counts = summary.get("counts", [])
    if not counts:
        base = f"Kibo Summary for {summary['date']}\nNo commands captured yet."
        return append_today_items(base, today)

    lines = [f"Kibo Summary for {summary['date']}"]
    for row in counts:
        lines.append(f"{row['intent']} / {row['status']}: {row['count']}")
    return append_today_items("\n".join(lines), today)


def format_today(today: dict) -> str:
    items = today.get("items", [])
    if not items:
        return f"Today ({today['date']})\nNo scheduled tasks, reminders, or events."

    lines = [f"Today ({today['date']})"]
    for item in items[:12]:
        payload = item.get("parsed_payload") or {}
        when = payload.get("datetime") or payload.get("date") or "today"
        text = item.get("raw_text", "").strip()
        url = item.get("external_url")
        line = f"- {item['intent']}: {text} ({when})"
        if url:
            line += f"\n  {url}"
        lines.append(line)
    return "\n".join(lines)


def format_week(week: dict) -> str:
    items = week.get("items", [])
    if not items:
        return f"Week ({week['start_date']} to {week['end_date']})\nNo upcoming tasks, reminders, or events."

    lines = [f"Week ({week['start_date']} to {week['end_date']})"]
    for item in items[:20]:
        payload = item.get("parsed_payload") or {}
        when = payload.get("datetime") or payload.get("date") or "scheduled"
        line = f"- {item['intent']}: {clean_raw_text(item.get('raw_text', ''))} ({when})"
        if item.get("external_url"):
            line += f"\n  {item['external_url']}"
        lines.append(line)
    return "\n".join(lines)


def format_search_results(query: str, rows: list[dict]) -> str:
    if not rows:
        return f"No Kibo results for: {query}"
    lines = [f"Search results for: {query}"]
    for row in rows[:8]:
        line = f"- {row['intent']}: {clean_raw_text(row.get('raw_text', ''))}"
        if row.get("external_url"):
            line += f"\n  {row['external_url']}"
        lines.append(line)
    return "\n".join(lines)


def format_open_result(query: str, row: dict | None) -> str:
    if not row:
        return f"I could not find anything matching: {query}"
    if row.get("external_url"):
        return f"{clean_raw_text(row.get('raw_text', ''))}\n{row['external_url']}"
    return f"I found a match, but it does not have a Notion URL: {clean_raw_text(row.get('raw_text', ''))}"


def clean_raw_text(text: str) -> str:
    for prefix in ("/task ", "/note ", "/link ", "/remind ", "/event "):
        if text.lower().startswith(prefix):
            return text[len(prefix) :].strip()
    return text.strip()


def append_today_items(base: str, today: dict | None) -> str:
    if not today:
        return base
    items = today.get("items", [])
    if not items:
        return f"{base}\n\nToday: no scheduled items."
    lines = [base, "", "Today:"]
    for item in items[:5]:
        payload = item.get("parsed_payload") or {}
        when = payload.get("datetime") or payload.get("date") or "today"
        lines.append(f"- {item['intent']}: {item.get('raw_text', '').strip()} ({when})")
    return "\n".join(lines)
