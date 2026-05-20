from app.config import Settings
from app.models.schemas import Intent
from app.services.google_calendar_service import GoogleCalendarService, default_end_datetime, reminder_minutes


def test_google_calendar_not_configured_returns_none() -> None:
    service = GoogleCalendarService(Settings())

    result = service.create_for_intent(
        Intent.EVENT,
        {"text": "Bote Blitz", "datetime": "2026-06-06T14:00:00-04:00"},
        "Bote Blitz",
    )

    assert result is None


def test_google_calendar_creates_event_with_popup_reminders(monkeypatch) -> None:
    captured = {}

    class TokenResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"access_token": "access-token"}

    class EventResponse:
        status_code = 200

        def json(self):
            return {"id": "event-id", "htmlLink": "https://calendar.google.com/event"}

    def fake_post(url, **kwargs):
        if url == "https://oauth2.googleapis.com/token":
            captured["token"] = kwargs
            return TokenResponse()
        captured["event_url"] = url
        captured["event"] = kwargs
        return EventResponse()

    monkeypatch.setattr("app.services.google_calendar_service.requests.post", fake_post)
    service = GoogleCalendarService(
        Settings(
            google_calendar_client_id="client-id",
            google_calendar_client_secret="client-secret",
            google_calendar_refresh_token="refresh-token",
            google_calendar_reminder_minutes="60,10,0",
        )
    )

    result = service.create_for_intent(
        Intent.EVENT,
        {
            "text": "Bote Blitz",
            "datetime": "2026-06-06T14:00:00-04:00",
            "end_datetime": "2026-06-06T18:00:00-04:00",
        },
        "Bote Blitz",
    )

    assert result.status == "succeeded"
    assert captured["event_url"].endswith("/calendars/primary/events")
    assert captured["event"]["json"]["summary"] == "Bote Blitz"
    assert captured["event"]["json"]["start"]["dateTime"] == "2026-06-06T14:00:00-04:00"
    assert captured["event"]["json"]["end"]["dateTime"] == "2026-06-06T18:00:00-04:00"
    assert captured["event"]["json"]["reminders"]["useDefault"] is False
    assert captured["event"]["json"]["reminders"]["overrides"] == [
        {"method": "popup", "minutes": 60},
        {"method": "popup", "minutes": 10},
        {"method": "popup", "minutes": 0},
    ]


def test_default_end_datetime() -> None:
    assert default_end_datetime("2026-06-06T14:00:00-04:00", minutes=30) == "2026-06-06T14:30:00-04:00"


def test_reminder_minutes_caps_at_five() -> None:
    settings = Settings(google_calendar_reminder_minutes="120,60,30,10,5,0")
    assert reminder_minutes(settings) == [120, 60, 30, 10, 5]
