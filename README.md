# Kibo

Kibo is a Telegram command center that turns quick messages into structured Notion records with a Supabase audit trail.

The current MVP is intentionally command-first:

- `/note <text>` saves an inbox note in Notion.
- `/task <text>` saves a task in Notion.
- `/link <url or text>` saves a read-later item in Notion.
- `/book <title or recommendation>` saves a book recommendation in Notion.
- `/remind <text>` saves a scheduled reminder in Notion.
- `/event <text>` saves a scheduled event in Notion.
- `/today` shows today's tasks, events, and reminders.
- `/week` shows upcoming tasks, events, and reminders for the next seven days.
- `/search <query>` searches captured Kibo records.
- `/open <query>` returns the best matching Notion URL.
- `/done <query>` marks a matching task, reminder, or event done in Notion.
- `/summary today` returns today's audit counts.
- `/help` shows supported commands.

Phase 3 adds hybrid natural capture. Deterministic rules handle obvious messages, and Anthropic handles uncertain natural language behind a confidence gate. These messages now work without slash commands when Kibo is confident:

```text
pay edenorte tomorrow
call elayne friday
save https://example.com
idea: greq pricing dashboard
remind me tomorrow at 9am to review invoices
meeting with Richard tomorrow at 5pm
mañana recuérdame revisar la factura de Edenorte a las 9am
```

If Kibo is unsure, it asks you to use an explicit slash command instead of guessing.

## Architecture

```text
Telegram polling bot
  -> command parser
  -> Kibo command handler
  -> Notion API
  -> Supabase Postgres schema kibo
```

Notion is the operating workspace. Supabase is the internal audit log.

## Setup

1. Create a Python virtual environment.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Copy env vars.

```bash
cp .env.example .env
```

3. Fill `.env`.

For Telegram, create the bot in Telegram with `@BotFather`, then paste the token into `TELEGRAM_BOT_TOKEN`.
After sending `/start` or `/help` to the bot from your own Telegram account, run:

```bash
python scripts/inspect_telegram_setup.py
```

Use the printed `Suggested TELEGRAM_ALLOWED_USER_IDS=...` value in `.env`.
Then configure the Telegram command menu:

```bash
python scripts/configure_telegram_bot.py
```

4. Apply the Supabase schema in `supabase/schema.sql` to the connected Supabase project. It only creates objects inside schema `kibo`.

5. Create the Notion databases under a Kibo parent page and put their database IDs in `.env`.

```bash
python scripts/create_notion_workspace.py
```

6. Run the polling bot.

```bash
python -m app.bot.polling
```

The polling bot also checks due reminders every 30 seconds and sends Telegram reminder messages once.

## Local API

The FastAPI app exposes health endpoints for deployment checks:

```bash
uvicorn app.main:app --reload
```

It also exposes the Telegram webhook endpoint:

```text
POST /telegram/webhook
```

For production, deploy the FastAPI app and register the webhook with:

```bash
python scripts/set_telegram_webhook.py
```

## Docs

- Product blueprint: `docs/kibo_app_blueprint.md`
- Notion CLI overview: `docs/notion-cli-ntn-overview.md`
- Google Calendar setup: `docs/google-calendar-setup.md`
- Render deployment: `docs/render-deploy.md`

## License

MIT
