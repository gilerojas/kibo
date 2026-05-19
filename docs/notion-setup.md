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

- `Task Board`: board grouped by `Status`
- `Open Tasks`: table sorted by `Due Date`

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

## Phase 2 dashboard baseline

The `KIBO COMMAND CENTER` parent page should include linked database views:

- `Dashboard - Inbox`
- `Dashboard - Tasks`
- `Dashboard - Schedule`
- `Dashboard - Read Later`
- `Dashboard - Logs`

The source databases should include these view tabs:

- `Kibo Inbox`: `Recent Notes`
- `Kibo Tasks`: `Task Board`, `Open Tasks`
- `Kibo Links`: `Read Later`, `Archive`
- `Kibo Schedule`: `Calendar`, `Upcoming`
- `Kibo Logs`: `Summaries`, `Errors`

Some view filters may need manual refinement in Notion because Notion status-filter support through the connector DSL can be limited. The important baseline is that the dashboard page now exposes the core operating databases directly.
