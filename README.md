# Kibo

Kibo is a Telegram command center that turns quick messages into structured Notion records with a Supabase audit trail.

The current MVP is intentionally command-first:

- `/note <text>` saves an inbox note in Notion.
- `/task <text>` saves a task in Notion.
- `/link <url or text>` saves a read-later item in Notion.
- `/remind <text>` saves a scheduled reminder in Notion.
- `/event <text>` saves a scheduled event in Notion.
- `/summary today` returns today's audit counts.
- `/help` shows supported commands.

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

4. Apply the Supabase schema in `supabase/schema.sql` to the connected Supabase project. It only creates objects inside schema `kibo`.

5. Create the Notion databases under a Kibo parent page and put their database IDs in `.env`.

```bash
export NOTION_API_KEY=secret_xxx
export KIBO_NOTION_PARENT_PAGE_ID=your_parent_page_id
python scripts/create_notion_workspace.py
```

6. Run the polling bot.

```bash
python -m app.bot.polling
```

## Local API

The FastAPI app exposes health endpoints for deployment checks:

```bash
uvicorn app.main:app --reload
```

## Docs

- Product blueprint: `docs/kibo_app_blueprint.md`
- Notion CLI overview: `docs/notion-cli-ntn-overview.md`

## License

MIT
