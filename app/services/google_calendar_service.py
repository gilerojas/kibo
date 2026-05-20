from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests

from app.config import Settings
from app.models.schemas import ActionResult, Intent


class GoogleCalendarService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.google_calendar_client_id
            and self.settings.google_calendar_client_secret
            and self.settings.google_calendar_refresh_token
        )

    def create_for_intent(self, intent: Intent, payload: dict[str, Any], raw_text: str) -> ActionResult | None:
        if not self.is_configured or intent not in {Intent.EVENT, Intent.REMINDER} or not payload.get("datetime"):
            return None

        title = str(payload.get("text") or raw_text).strip()
        start = str(payload["datetime"])
        end = str(payload.get("end_datetime") or default_end_datetime(start, minutes=30 if intent == Intent.REMINDER else 60))
        event_body = {
            "summary": title,
            "description": f"Created by Kibo from Telegram.\n\n{raw_text}",
            "start": {"dateTime": start, "timeZone": self.settings.default_timezone},
            "end": {"dateTime": end, "timeZone": self.settings.default_timezone},
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": minutes} for minutes in reminder_minutes(self.settings)],
            },
        }

        try:
            access_token = self._access_token()
            calendar_id = quote(self.settings.google_calendar_id or "primary", safe="")
            response = requests.post(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json=event_body,
                timeout=20,
            )
            if response.status_code >= 400:
                return ActionResult(
                    "google_calendar",
                    intent.value,
                    "failed",
                    error_message=f"Google Calendar API returned {response.status_code}",
                )
            data = response.json()
            return ActionResult(
                "google_calendar",
                intent.value,
                "succeeded",
                external_id=data.get("id"),
                external_url=data.get("htmlLink"),
            )
        except Exception as exc:
            return ActionResult("google_calendar", intent.value, "failed", error_message=str(exc)[:1000])

    def _access_token(self) -> str:
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.settings.google_calendar_client_id,
                "client_secret": self.settings.google_calendar_client_secret,
                "refresh_token": self.settings.google_calendar_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=20,
        )
        response.raise_for_status()
        return str(response.json()["access_token"])


def default_end_datetime(start: str, *, minutes: int) -> str:
    start_dt = datetime.fromisoformat(start)
    return (start_dt + timedelta(minutes=minutes)).isoformat()


def reminder_minutes(settings: Settings) -> list[int]:
    values: list[int] = []
    for raw in settings.google_calendar_reminder_minutes.split(","):
        raw = raw.strip()
        if not raw:
            continue
        values.append(max(0, int(raw)))
    return values[:5] or [30, 0]
