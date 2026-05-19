from __future__ import annotations

from functools import lru_cache

from app.bot.telegram_client import TelegramClient
from app.config import get_settings
from app.db.repository import SupabaseRepository
from app.services.handlers import KiboHandler
from app.services.notion_service import NotionService


@lru_cache
def get_runtime() -> tuple[TelegramClient, KiboHandler]:
    settings = get_settings()
    settings.require_runtime()
    telegram = TelegramClient(settings.telegram_bot_token)
    repository = SupabaseRepository(settings)
    handler = KiboHandler(settings, repository, NotionService(settings))
    return telegram, handler
