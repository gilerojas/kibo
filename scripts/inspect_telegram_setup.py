from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_dotenv_file


def main() -> int:
    load_dotenv_file(str(PROJECT_ROOT / ".env"))
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN is missing in .env.", file=sys.stderr)
        print("Create the bot with @BotFather, paste the token into .env, then run this again.", file=sys.stderr)
        return 1

    client = TelegramSetupClient(token)
    bot = client.get_me()
    print(f"Bot: @{bot.get('username')} ({bot.get('first_name')})")
    print(f"Bot ID: {bot.get('id')}")

    updates = client.get_updates()
    users = extract_users(updates)
    if not users:
        print("No recent Telegram messages found.")
        print("Send /start or /help to the bot from your Telegram account, then run this again.")
        return 0

    print("Recent Telegram users:")
    for user in users:
        name_parts = [user.get("first_name"), user.get("last_name")]
        display_name = " ".join(part for part in name_parts if part) or "(no name)"
        username = f"@{user['username']}" if user.get("username") else "(no username)"
        print(f"- user_id={user['id']} username={username} name={display_name}")

    if not os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").strip():
        user_ids = ",".join(str(user["id"]) for user in users)
        print(f"Suggested TELEGRAM_ALLOWED_USER_IDS={user_ids}")
    return 0


class TelegramSetupClient:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"

    def get_me(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/getMe", timeout=15)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getMe failed: {payload}")
        return payload["result"]

    def get_updates(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/getUpdates",
            params={"allowed_updates": ["message"], "limit": 20, "timeout": 0},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getUpdates failed: {payload}")
        return payload.get("result", [])


def extract_users(updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    users_by_id: dict[int, dict[str, Any]] = {}
    for update in updates:
        user = ((update.get("message") or {}).get("from") or {}).copy()
        user_id = user.get("id")
        if isinstance(user_id, int) and not user.get("is_bot"):
            users_by_id[user_id] = user
    return list(users_by_id.values())


if __name__ == "__main__":
    raise SystemExit(main())
