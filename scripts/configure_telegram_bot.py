from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_dotenv_file


BOT_COMMANDS = [
    {"command": "start", "description": "Start Kibo"},
    {"command": "note", "description": "Save a note to Notion"},
    {"command": "task", "description": "Create a task"},
    {"command": "link", "description": "Save a read-later link"},
    {"command": "remind", "description": "Create a reminder"},
    {"command": "event", "description": "Create a scheduled event"},
    {"command": "summary", "description": "Show today's capture summary"},
    {"command": "help", "description": "Show supported commands"},
]


def main() -> int:
    load_dotenv_file(str(PROJECT_ROOT / ".env"))
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN is missing in .env.", file=sys.stderr)
        return 1

    response = requests.post(
        f"https://api.telegram.org/bot{token}/setMyCommands",
        json={"commands": BOT_COMMANDS, "scope": {"type": "all_private_chats"}},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        print(f"Telegram setMyCommands failed: {payload}", file=sys.stderr)
        return 1

    print("Telegram command menu configured for private chats.")
    print("In BotFather, keep Privacy Mode enabled and do not add Kibo to groups for the MVP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
