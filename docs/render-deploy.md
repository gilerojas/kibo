# Render Deployment

Phase 5 uses Telegram webhooks on a Render web service.

## Render service

Use `render.yaml` or create a web service manually.

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health check:

```text
/health
```

## Required environment variables

Set these in Render:

```bash
APP_ENV=production
APP_BASE_URL=https://your-render-service.onrender.com
DEFAULT_TIMEZONE=America/Santo_Domingo
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=...
TELEGRAM_WEBHOOK_SECRET=...
SUPABASE_DATABASE_URL=...
NOTION_API_KEY=...
NOTION_INBOX_DATABASE_ID=...
NOTION_TASKS_DATABASE_ID=...
NOTION_LINKS_DATABASE_ID=...
NOTION_SCHEDULE_DATABASE_ID=...
NOTION_LOGS_DATABASE_ID=...
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

Generate `TELEGRAM_WEBHOOK_SECRET` locally with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Register the Telegram webhook

After Render deploys and `APP_BASE_URL` is set:

```bash
python scripts/set_telegram_webhook.py
```

The script calls Telegram `setWebhook` with:

```text
{APP_BASE_URL}/telegram/webhook
```

It also sends the secret token, so the FastAPI route rejects calls without Telegram's `X-Telegram-Bot-Api-Secret-Token` header.

## Local polling fallback

For local development, delete the webhook first:

```bash
python scripts/delete_telegram_webhook.py
python -m app.bot.polling
```

Telegram only reliably uses one delivery mode at a time. Use webhook in production and polling only for local fallback.
