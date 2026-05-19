from __future__ import annotations

import logging
import time
from datetime import datetime

from app.bot.telegram_client import TelegramClient, telegram_message_from_update
from app.config import get_settings
from app.db.repository import SupabaseRepository
from app.runtime import get_runtime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kibo.polling")


def run_polling() -> None:
    settings = get_settings()
    settings.require_runtime()

    telegram, handler = get_runtime()
    repository = SupabaseRepository(settings)

    offset: int | None = None
    offset = initial_offset(telegram, settings)
    last_reminder_check = 0.0
    logger.info("Starting Kibo Telegram polling")
    while True:
        try:
            now_monotonic = time.monotonic()
            if now_monotonic - last_reminder_check >= 30:
                send_due_reminders(repository, telegram, settings)
                last_reminder_check = now_monotonic

            updates = telegram.get_updates(offset=offset, timeout=settings.telegram_poll_timeout_seconds)
            for update in updates:
                offset = int(update["update_id"]) + 1
                message = telegram_message_from_update(update, tz=settings.tzinfo)
                if message is None:
                    continue
                try:
                    response_text = handler.handle(message)
                except Exception:
                    logger.exception("Failed to process Telegram update %s", update.get("update_id"))
                    response_text = "Kibo hit an internal error while processing this command."
                telegram.send_message(message.chat_id, response_text)
        except KeyboardInterrupt:
            logger.info("Stopping Kibo Telegram polling")
            raise
        except Exception:
            logger.exception("Polling loop failed; retrying soon")
            time.sleep(5)


def send_due_reminders(repository: SupabaseRepository, telegram: TelegramClient, settings) -> None:
    due = repository.due_reminders(datetime.now(settings.tzinfo), limit=10)
    for reminder in due:
        text = f"Reminder: {reminder['title']}"
        if reminder.get("notion_url"):
            text += f"\n{reminder['notion_url']}"
        try:
            telegram.send_message(int(reminder["telegram_chat_id"]), text)
            repository.mark_reminder_sent(reminder["id"])
        except Exception as exc:
            logger.exception("Failed to send reminder %s", reminder["id"])
            repository.mark_reminder_failed(reminder["id"], str(exc))


def initial_offset(telegram: TelegramClient, settings) -> int | None:
    updates = telegram.get_updates(offset=None, timeout=0)
    if not updates:
        return None
    return max(int(update["update_id"]) for update in updates) + 1


if __name__ == "__main__":
    run_polling()
