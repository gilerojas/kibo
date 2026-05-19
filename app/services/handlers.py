from __future__ import annotations

from datetime import datetime

from app.config import Settings
from app.models.schemas import ActionResult, CommandStatus, Intent, TelegramMessage
from app.services.auth import is_authorized_user
from app.services.parser import HELP_TEXT, parse_command


class KiboHandler:
    def __init__(
        self,
        settings: Settings,
        repository,
        notion,
    ):
        self.settings = settings
        self.repository = repository
        self.notion = notion

    def handle(self, message: TelegramMessage) -> str:
        parsed = parse_command(message.text, now=datetime.now(self.settings.tzinfo))

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
        command_id = self.repository.create_command(user_id=user_id, message=message, parsed=parsed)

        if parsed.error:
            self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message=parsed.error)
            return parsed.error

        if parsed.intent == Intent.HELP:
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return HELP_TEXT

        if parsed.intent == Intent.SUMMARY:
            summary = self.repository.summary_for_day(user_id, datetime.now(self.settings.tzinfo).date())
            response = format_summary(summary)
            log_result = self.notion.create_log(f"Kibo Summary {summary['date']}", response)
            self.repository.create_action(command_id=command_id, user_id=user_id, result=log_result)
            self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
            return response

        if parsed.intent in {Intent.NOTE, Intent.TASK, Intent.LINK, Intent.REMINDER, Intent.EVENT}:
            result = self.notion.create_for_intent(parsed.intent, parsed.parsed_payload, parsed.raw_text)
            self.repository.create_action(command_id=command_id, user_id=user_id, result=result)
            if result.status == "succeeded":
                self.repository.update_command_status(command_id, CommandStatus.PROCESSED)
                return confirmation_for(parsed.intent, parsed.body, result.external_url)
            self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message=result.error_message)
            return "I saved the command, but Notion could not create the item. Check the Notion integration and database IDs."

        self.repository.update_command_status(command_id, CommandStatus.FAILED, error_message="Unsupported command")
        return "Unsupported command. Try /help."


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


def format_summary(summary: dict) -> str:
    counts = summary.get("counts", [])
    if not counts:
        return f"Kibo Summary for {summary['date']}\nNo commands captured yet."

    lines = [f"Kibo Summary for {summary['date']}"]
    for row in counts:
        lines.append(f"{row['intent']} / {row['status']}: {row['count']}")
    return "\n".join(lines)
