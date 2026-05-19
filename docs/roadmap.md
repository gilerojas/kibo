# Kibo Roadmap

Kibo's MVP proves the pipe works: Telegram messages can create Notion records and Supabase audit rows. The next goal is usefulness: Kibo should help run the day, not just save items.

## Phase 1: Daily Operating Loop

Status: Completed for MVP

Goal: make Kibo useful every morning and throughout the day.

Build:

- `/today`: show today's due tasks, reminders, events, and failed commands.
- Timed Telegram reminders: send a Telegram message when a scheduled item is due.
- Reminder status tracking: mark reminders as `sent`, `done`, or `cancelled`.
- Summary upgrade: make `/summary today` include useful next actions, not just counts.

Acceptance:

- Sending `/today` returns a clean list of today's open work.
- A `/remind Review invoices tomorrow at 9am` item sends a Telegram reminder at the correct time.
- Sent reminders are not sent repeatedly.

## Phase 2: Notion Command Center

Status: Completed baseline

Goal: make the Notion workspace valuable when opened directly.

Build:

- Create or document views for:
  - Today
  - This Week
  - Waiting
  - Read Later
  - Ideas
  - Scheduled
  - Done
  - Failed Commands
- Add dashboard guidance for the `Kibo Command Center` parent page.
- Add status cleanup conventions across Tasks, Schedule, Links, and Logs.

Acceptance:

- Opening Notion shows a practical dashboard without needing to search databases manually.
- Tasks and reminders can be reviewed by date/status.
- Failed commands are visible for debugging.

Implemented baseline:

- Parent page linked views: `Dashboard - Inbox`, `Dashboard - Tasks`, `Dashboard - Schedule`, `Dashboard - Read Later`, `Dashboard - Logs`.
- Database views: `Recent Notes`, `Task Board`, `Open Tasks`, `Calendar`, `Upcoming`, `Read Later`, `Archive`, `Summaries`, `Errors`.
- Schedule database has a calendar view by `Scheduled For`.

## Phase 3: Natural Capture

Status: Completed baseline

Goal: reduce command friction.

Build:

- Classify messages without prefixes into `note`, `task`, `link`, `reminder`, `event`, or `unknown`.
- Extract simple dates and times from natural text.
- Ask a clarification question when intent is ambiguous.
- Keep slash commands as the reliable fallback.

Examples:

```text
pay edenorte tomorrow
call elayne friday
save https://example.com
idea: greq pricing dashboard
```

Acceptance:

- Common unprefixed messages are routed correctly.
- Low-confidence messages do not create incorrect records silently.
- Slash commands keep working exactly as before.

Implemented baseline:

- URLs become links.
- `idea:` and `note:` messages become notes.
- Action verbs such as `pay`, `call`, `review`, `check`, and `send` become tasks.
- `remind me`, `reminder`, and `remember to` become reminders when a date or time is present.
- Meeting/event language with a date or time becomes a scheduled event.
- Ambiguous messages ask for an explicit slash command instead of guessing.
- Anthropic-backed LLM parsing handles natural language when rules are uncertain, including Spanish phrasing.
- LLM results execute only when confidence is at least `0.80`; lower-confidence results ask for clarification.

## Phase 4: Task Control Commands

Status: Completed baseline

Goal: let Kibo manage captured work, not just create it.

Build:

- `/done <text>`: find and mark a matching task/reminder done.
- `/search <query>`: search recent commands and Notion records.
- `/open <query>`: return the best matching Notion URL.
- `/week`: show upcoming tasks and reminders for the next seven days.

Acceptance:

- User can complete and retrieve work from Telegram.
- Search results are short, ranked, and include Notion links.
- Ambiguous matches ask the user to choose.

Implemented baseline:

- `/week` shows upcoming tasks, reminders, and events for the next seven days.
- `/search <query>` searches processed Kibo records and returns matching Notion links.
- `/open <query>` returns the best matching Notion URL.
- `/done <query>` marks the best matching task/reminder/event as `Done` in Notion.

## Phase 5: Always-On Deployment

Status: Active / webhook baseline

Goal: make Kibo reliable without a local laptop.

Build:

- Deploy the FastAPI/polling worker to Render or Railway.
- Configure production env vars.
- Add startup health checks.
- Add basic error logging and failure summaries.
- Document restart/redeploy steps.

Acceptance:

- Telegram bot stays online after the local terminal is closed.
- Supabase and Notion calls work from production.
- Failures are logged in Supabase and optionally mirrored to Notion Logs.

Implemented baseline:

- FastAPI Telegram webhook route at `POST /telegram/webhook`.
- Telegram webhook secret header validation.
- Render web service config in `render.yaml`.
- Webhook setup/delete scripts for switching between production webhook and local polling.

## Phase 6: Intelligence Layer

Goal: turn captured items into prioritized action.

Build:

- Daily digest with recommended top actions.
- Weekly review summary.
- Basic tag/area detection for Personal, GREQ, SolQuim, sophIA, Finance, Operations, and Admin.
- Optional LLM parser behind a strict JSON schema.

Acceptance:

- Daily digest is actionable, not just a count report.
- Tasks are grouped by area and urgency.
- LLM parsing failures fall back to safe clarification instead of bad writes.

## Near-Term Priority

Build in this order:

1. Natural capture
2. `/done` and `/search`
3. Deployment
4. Daily digest intelligence

This sequence turns Kibo from a capture bot into a daily operating assistant.
