from __future__ import annotations

import logging
import time

from app.bot.telegram_client import TelegramClient, telegram_message_from_update
from app.config import get_settings
from app.db.repository import SupabaseRepository
from app.services.handlers import KiboHandler
from app.services.notion_service import NotionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kibo.polling")


def run_polling() -> None:
    settings = get_settings()
    settings.require_runtime()

    telegram = TelegramClient(settings.telegram_bot_token)
    handler = KiboHandler(settings, SupabaseRepository(settings), NotionService(settings))

    offset: int | None = None
    logger.info("Starting Kibo Telegram polling")
    while True:
        try:
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


if __name__ == "__main__":
    run_polling()
