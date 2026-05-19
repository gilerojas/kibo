import os
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import ZoneInfo


@dataclass
class Settings:
    app_env: str = "development"
    default_timezone: str = "America/Santo_Domingo"

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    telegram_poll_timeout_seconds: int = 25

    supabase_database_url: str = ""

    notion_api_key: str = ""
    notion_inbox_database_id: str = ""
    notion_tasks_database_id: str = ""
    notion_links_database_id: str = ""
    notion_schedule_database_id: str = ""
    notion_logs_database_id: str = ""
    notion_api_version: str = "2022-06-28"

    @property
    def allowed_user_ids(self) -> set[int]:
        values: set[int] = set()
        for raw in self.telegram_allowed_user_ids.split(","):
            raw = raw.strip()
            if raw:
                values.add(int(raw))
        return values

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.default_timezone)

    def require_runtime(self) -> None:
        missing = [
            name
            for name, value in {
                "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
                "TELEGRAM_ALLOWED_USER_IDS": self.telegram_allowed_user_ids,
                "SUPABASE_DATABASE_URL": self.supabase_database_url,
                "NOTION_API_KEY": self.notion_api_key,
                "NOTION_INBOX_DATABASE_ID": self.notion_inbox_database_id,
                "NOTION_TASKS_DATABASE_ID": self.notion_tasks_database_id,
                "NOTION_LINKS_DATABASE_ID": self.notion_links_database_id,
                "NOTION_SCHEDULE_DATABASE_ID": self.notion_schedule_database_id,
                "NOTION_LOGS_DATABASE_ID": self.notion_logs_database_id,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    load_dotenv_file(".env")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "America/Santo_Domingo"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_allowed_user_ids=os.getenv("TELEGRAM_ALLOWED_USER_IDS", ""),
        telegram_poll_timeout_seconds=int(os.getenv("TELEGRAM_POLL_TIMEOUT_SECONDS", "25")),
        supabase_database_url=os.getenv("SUPABASE_DATABASE_URL", ""),
        notion_api_key=os.getenv("NOTION_API_KEY", ""),
        notion_inbox_database_id=os.getenv("NOTION_INBOX_DATABASE_ID", ""),
        notion_tasks_database_id=os.getenv("NOTION_TASKS_DATABASE_ID", ""),
        notion_links_database_id=os.getenv("NOTION_LINKS_DATABASE_ID", ""),
        notion_schedule_database_id=os.getenv("NOTION_SCHEDULE_DATABASE_ID", ""),
        notion_logs_database_id=os.getenv("NOTION_LOGS_DATABASE_ID", ""),
        notion_api_version=os.getenv("NOTION_API_VERSION", "2022-06-28"),
    )


def load_dotenv_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
