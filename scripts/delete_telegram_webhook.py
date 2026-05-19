from __future__ import annotations

import os
import sys

import requests

from app.config import load_dotenv_file


def main() -> int:
    load_dotenv_file(".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN first.", file=sys.stderr)
        return 1

    response = requests.post(
        f"https://api.telegram.org/bot{token}/deleteWebhook",
        json={"drop_pending_updates": True},
        timeout=20,
    )
    print(response.status_code)
    print(response.text)
    response.raise_for_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
