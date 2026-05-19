# Kibo Notion Setup

Create or provide a parent page named `Kibo Command Center`, then create these databases under it.

The runtime app expects each database to have the exact property names below.

## Kibo Inbox

- `Name`: title
- `Type`: select with `Note`
- `Content`: rich text
- `Source`: select with `Telegram`

## Kibo Tasks

- `Name`: title
- `Status`: status with `Inbox`, `Active`, `Done`
- `Due Date`: date
- `Source`: select with `Telegram`

Recommended views:

- `All Tasks`: table
- `Task Board`: board grouped by `Status`

## Kibo Links

- `Name`: title
- `URL`: url
- `Status`: status with `Inbox`, `Read`, `Archived`
- `Source`: select with `Telegram`

## Kibo Schedule

- `Name`: title
- `Type`: select with `Reminder`, `Event`
- `Status`: status with `Scheduled`, `Done`, `Cancelled`
- `Scheduled For`: date
- `Source`: select with `Telegram`

Recommended views:

- `Calendar`: calendar by `Scheduled For`
- `Upcoming`: table sorted by `Scheduled For`

## Kibo Logs

- `Name`: title
- `Type`: select with `Summary`, `Error`, `System`
- `Content`: rich text

## Connector setup

The connected Notion plugin can create these databases once the parent page URL/ID is available. After creation, copy each database ID into `.env`.

The official Notion CLI (`ntn`) can also inspect and manage the workspace, but it is not required by the runtime app.
