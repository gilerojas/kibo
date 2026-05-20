from __future__ import annotations

import os
import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_dotenv_file


SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://127.0.0.1:8080/callback"


class CallbackHandler(BaseHTTPRequestHandler):
    code: str | None = None
    error: str | None = None
    expected_state: str = ""

    def do_GET(self) -> None:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        state = query.get("state", [""])[0]
        if state != self.expected_state:
            self.__class__.error = "OAuth state mismatch"
        elif query.get("error"):
            self.__class__.error = query["error"][0]
        else:
            self.__class__.code = query.get("code", [""])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"You can close this tab and return to the terminal.")

    def log_message(self, format: str, *args) -> None:
        return


def main() -> int:
    load_dotenv_file(str(PROJECT_ROOT / ".env"))
    client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET in .env first.", file=sys.stderr)
        return 1

    state = secrets.token_urlsafe(24)
    CallbackHandler.expected_state = state
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )

    print("Opening Google OAuth consent page...")
    print(auth_url)
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", 8080), CallbackHandler)
    server.handle_request()
    if CallbackHandler.error or not CallbackHandler.code:
        print(f"OAuth failed: {CallbackHandler.error or 'missing code'}", file=sys.stderr)
        return 1

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": CallbackHandler.code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=20,
    )
    response.raise_for_status()
    token = response.json().get("refresh_token")
    if not token:
        print("Google did not return a refresh token. Re-run with prompt=consent or remove prior app access.", file=sys.stderr)
        return 1
    print("\nAdd this to .env and Render:")
    print(f"GOOGLE_CALENDAR_REFRESH_TOKEN={token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
