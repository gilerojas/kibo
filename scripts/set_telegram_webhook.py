from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import load_dotenv_file


def main() -> int:
    load_dotenv_file(".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not token or not base_url or not secret:
        print("Set TELEGRAM_BOT_TOKEN, APP_BASE_URL, and TELEGRAM_WEBHOOK_SECRET first.", file=sys.stderr)
        return 1

    webhook_url = f"{base_url}/telegram/webhook"
    response = requests.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        json={
            "url": webhook_url,
            "secret_token": secret,
            "allowed_updates": ["message"],
            "drop_pending_updates": True,
        },
        timeout=20,
    )
    print(response.status_code)
    print(response.text)
    response.raise_for_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
