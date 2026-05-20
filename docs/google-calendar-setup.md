# Google Calendar Setup

Kibo can use Notion as the dashboard and Google Calendar as the notification engine for timed `/event` and `/remind` items.

## Google Cloud

1. Create or open a Google Cloud project.
2. Enable the Google Calendar API.
3. Configure the OAuth consent screen.
4. Create an OAuth Client ID.
5. Use application type `Desktop app` for local setup.

## Local Token Setup

Add these values to `.env`:

```bash
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
GOOGLE_CALENDAR_ID=primary
GOOGLE_CALENDAR_REMINDER_MINUTES=30,0
```

Then run:

```bash
python scripts/create_google_calendar_token.py
```

Complete the browser consent flow. The script prints:

```bash
GOOGLE_CALENDAR_REFRESH_TOKEN=...
```

Add that value to local `.env` and to Render.

## Runtime Behavior

When Google Calendar env vars are configured:

- `/event` with a datetime creates a Notion schedule record and a Google Calendar event.
- `/remind` with a datetime creates a Notion schedule record, a Supabase reminder row, and a Google Calendar event.
- Google Calendar popup reminders use `GOOGLE_CALENDAR_REMINDER_MINUTES`.

Kibo does not create Google Calendar entries for notes, books, links, or untimed tasks.
