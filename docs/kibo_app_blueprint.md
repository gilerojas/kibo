# Kibo App Blueprint

## 1. Project Overview

**Kibo** is a Telegram-based productivity command center that turns quick messages into structured actions across Notion, Google Calendar, email, and a backend database.

The core idea is simple:

> Kibo converts scattered thoughts into organized actions.

Instead of opening multiple apps to save notes, create tasks, schedule meetings, or set reminders, the user sends a message to Kibo through Telegram. Kibo interprets the message, identifies the intent, routes it to the correct app, confirms the action, and stores a complete audit trail.

---

## 2. Brand Concept

### Name

**Kibo**

### Meaning

Kibo has two useful brand associations:

1. **Kibō** in Japanese means **hope**.
2. **Kibo** is the highest volcanic cone of Mount Kilimanjaro, associated with height, ambition, vision, and ascent.

### Brand Interpretation

**Kibo = hope + clarity + execution.**

For this product, Kibo represents an assistant that helps users move from intention to action.

### Tagline Options

- **From message to action.**
- **Your command center for getting things done.**
- **Turn thoughts into tasks, notes, and events.**
- **Capture fast. Organize automatically. Follow up reliably.**

---

## 3. Product Vision

Kibo should become a lightweight AI operations layer for personal and professional productivity.

The initial product is personal:

```text
Telegram → Notion → Google Calendar → Email
```

The scalable version is operational:

```text
Telegram → Notion → Calendar → Email → CRM → Business workflows
```

Long-term, Kibo can evolve from a personal productivity assistant into a business command center for founders, operators, consultants, students, freelancers, and small teams.

---

## 4. Problem Statement

Many people already use messaging apps as informal productivity systems. They send themselves notes, links, tasks, ideas, reminders, and follow-ups.

The problem is that chats are not structured databases.

Common issues:

- Tasks get buried under newer messages.
- Links are saved but never reviewed.
- Notes lack categories, tags, or follow-up status.
- Reminders are written but not triggered.
- Calendar events require manual app switching.
- Ideas are captured but not converted into projects or actions.
- Users lose time deciding where to store each item.

Kibo solves this by keeping the speed of chat while adding structure, routing, and follow-up.

---

## 5. Core Value Proposition

Kibo lets users send one message from their phone and automatically create the correct productivity object.

Example:

```text
Book meeting with Richard today from 5:30 to 6:30
```

Kibo should understand this as:

```json
{
  "intent": "calendar_event",
  "title": "Meeting with Richard",
  "start_time": "2026-05-18T17:30:00",
  "end_time": "2026-05-18T18:30:00",
  "destination": "google_calendar"
}
```

Then Kibo creates the calendar event and confirms it in Telegram.

---

## 6. Target Users

### Primary Users

- Founders
- Operators
- Consultants
- Freelancers
- Students
- Knowledge workers
- Productivity enthusiasts
- Notion users
- Telegram power users

### Secondary Users

- Small business teams
- Sales teams
- Operations teams
- Administrative assistants
- Project managers
- AI automation builders

### Ideal Early User Profile

A strong early user is someone who:

- Lives on their phone.
- Uses Telegram or WhatsApp frequently.
- Already saves notes in chats.
- Uses Notion, Google Calendar, or Gmail.
- Needs fast capture and reliable follow-up.
- Has multiple projects, meetings, and tasks.

---

## 7. Product Scope

### Version 1 Scope

Kibo should support these basic intents:

1. Notes
2. Tasks
3. Links
4. Reminders
5. Calendar events
6. Daily or weekly summaries

### Out of Scope for Version 1

- Full CRM
- Team permissions
- Payments
- WhatsApp integration
- Complex project management
- Voice transcription
- File uploads
- Multi-user billing
- Native mobile app

These can be added later after the MVP is stable.

---

## 8. Core User Flows

### Flow 1: Save a Note

User sends:

```text
Note: idea for sophIA payments dashboard
```

Kibo should:

1. Detect intent as `note`.
2. Clean the text.
3. Save the note in Notion.
4. Store the raw message in the database.
5. Reply with confirmation in Telegram.

Expected reply:

```text
Saved as note in Notion: idea for sophIA payments dashboard
```

---

### Flow 2: Create a Task

User sends:

```text
Task: call Elayne tomorrow about pending invoices
```

Kibo should:

1. Detect intent as `task`.
2. Extract task title.
3. Extract due date if present.
4. Create a task in Notion.
5. Save a backup record in the database.
6. Confirm in Telegram.

Expected reply:

```text
Task created: Call Elayne about pending invoices. Due: tomorrow.
```

---

### Flow 3: Save a Link

User sends:

```text
Read later: https://example.com/article
```

Kibo should:

1. Detect URL.
2. Classify as `link` or `read_later`.
3. Save to Notion Read Later database.
4. Optionally fetch page title.
5. Confirm in Telegram.

Expected reply:

```text
Link saved to Read Later.
```

---

### Flow 4: Create a Reminder

User sends:

```text
Remind me tomorrow at 8am to check Banco Popular rate
```

Kibo should:

1. Detect intent as `reminder`.
2. Extract reminder message.
3. Extract date and time.
4. Create a Google Calendar reminder event or Notion reminder.
5. Store record in the database.
6. Confirm in Telegram.

Expected reply:

```text
Reminder created for tomorrow at 8:00 AM: check Banco Popular rate.
```

Recommended rule:

- Use **Google Calendar** for exact timed reminders.
- Use **Notion** for tasks with due dates but no exact time.

---

### Flow 5: Create Calendar Event

User sends:

```text
Book meeting with Richard today from 5:30 to 6:30
```

Kibo should:

1. Detect intent as `calendar_event`.
2. Extract title.
3. Extract start and end time.
4. Create Google Calendar event.
5. Add default notification.
6. Confirm in Telegram.

Expected reply:

```text
Calendar event created: Meeting with Richard, today from 5:30 PM to 6:30 PM.
```

---

### Flow 6: Daily Summary

User sends:

```text
Summary of today
```

Kibo should:

1. Query the database and Notion.
2. Collect today's notes, tasks, reminders, links, and events.
3. Send a concise Telegram digest.

Expected reply:

```text
Today’s Kibo Summary

Tasks created: 3
Notes saved: 4
Links saved: 2
Calendar events: 1
Pending reminders: 2
```

---

## 9. Command Syntax for MVP

Version 1 should support explicit command prefixes to reduce ambiguity.

Recommended commands:

```text
/note
/task
/link
/remind
/event
/summary
/help
```

Examples:

```text
/note Idea for a new content calendar system
/task Call supplier tomorrow
/link https://example.com
/remind Review inventory Friday at 9am
/event Meeting with Richard today 5:30pm-6:30pm
/summary today
```

Natural language should be added after the structured commands are reliable.

---

## 10. Natural Language Layer

After MVP, Kibo should support natural commands without prefixes.

Examples:

```text
Book a meeting with Richard tomorrow from 5 to 6.
Remind me Monday at 8am to check payroll.
Save this link for later: https://example.com.
Create a task to review pending invoices next Friday.
```

The natural language layer should classify messages into one of these intents:

```text
note
task
link
reminder
calendar_event
summary
unknown
```

If confidence is low, Kibo should ask a clarification question.

Example:

```text
I can save this as a task or a note. Which one do you prefer?
```

---

## 11. System Architecture

### Recommended Architecture

```text
Telegram Bot
   ↓
Cloud Backend
   ↓
Intent Parser
   ↓
Action Router
   ├── Notion API
   ├── Google Calendar API
   ├── Gmail API / SMTP
   └── Database
```

### Suggested Stack

```text
Backend: FastAPI
Language: Python
Database: Supabase PostgreSQL or PostgreSQL
Hosting: Render, Railway, Fly.io, or Vercel serverless alternative
Bot: Telegram Bot API
Notes/Tasks: Notion API
Events: Google Calendar API
Email: Gmail API or SMTP
AI Parser: OpenAI, Anthropic, or local rule-based parser for MVP
```

### Why FastAPI

FastAPI is a good fit because:

- It is clean for API development.
- It supports webhooks well.
- It works naturally with Python integrations.
- It is easy to test locally.
- It can scale from MVP to production.

---

## 12. Main Components

### 12.1 Telegram Bot Interface

Responsibilities:

- Receive user messages.
- Send confirmations.
- Ask clarifying questions.
- Send summaries.
- Receive button responses in later versions.

Required features:

- Webhook endpoint.
- Chat ID validation.
- User authorization.
- Message logging.
- Error handling.

---

### 12.2 Intent Parser

Responsibilities:

- Identify message type.
- Extract dates, times, URLs, titles, and tags.
- Return structured JSON.

MVP approach:

- Rule-based parser using command prefixes.

Later approach:

- LLM-based parser with schema validation.

Example output:

```json
{
  "intent": "task",
  "title": "Call Elayne about pending invoices",
  "due_date": "2026-05-19",
  "priority": "medium",
  "area": "GREQ",
  "tags": ["finance", "follow-up"]
}
```

---

### 12.3 Action Router

Responsibilities:

- Decide which integration should receive the command.
- Create records in external apps.
- Handle success/failure responses.
- Save audit log.

Routing rules:

```text
note → Notion Inbox
link → Notion Read Later
task → Notion Tasks
reminder with exact time → Google Calendar
event → Google Calendar
summary → Database query + Telegram response
```

---

### 12.4 Notion Integration

Responsibilities:

- Create tasks.
- Save notes.
- Save links.
- Store project ideas.
- Maintain an organized workspace.

Suggested databases:

1. Kibo Inbox
2. Kibo Tasks
3. Kibo Read Later
4. Kibo Ideas
5. Kibo Logs

---

### 12.5 Google Calendar Integration

Responsibilities:

- Create calendar events.
- Create timed reminders.
- Add default notifications.
- Handle start/end dates and time zones.

Default timezone:

```text
America/Santo_Domingo
```

Recommended default reminders:

- Events: 15 minutes before.
- Timed reminders: at event time.

---

### 12.6 Email Integration

Responsibilities:

- Send daily or weekly summaries.
- Send optional confirmation emails.
- Send follow-up digests.

Initial use cases:

- Daily summary at 7:00 PM.
- Weekly review every Sunday.
- Missed tasks digest.

---

### 12.7 Database Layer

The database should be the internal source of truth.

Even if Notion or Google Calendar receives the final object, Kibo should store every command in its own database.

Purpose:

- Audit trail.
- Debugging.
- Analytics.
- Recovery.
- User history.
- Future dashboard.

---

## 13. Suggested Database Schema

### Table: users

```text
id
telegram_user_id
telegram_chat_id
name
email
timezone
notion_user_id
google_account_email
created_at
updated_at
is_active
```

### Table: commands

```text
id
user_id
raw_text
intent
status
parsed_payload
source
created_at
processed_at
error_message
```

### Table: actions

```text
id
command_id
user_id
action_type
destination
external_id
external_url
status
created_at
error_message
```

### Table: reminders

```text
id
user_id
command_id
title
reminder_at
status
calendar_event_id
created_at
completed_at
```

### Table: app_connections

```text
id
user_id
provider
access_token_encrypted
refresh_token_encrypted
scopes
created_at
updated_at
expires_at
```

---

## 14. Notion Workspace Design

### Main Database: Kibo Command Inbox

Properties:

```text
Title
Type
Status
Priority
Area
Due Date
Reminder Time
Source
URL
Telegram Message ID
Created At
Processed
External ID
Tags
```

### Type Options

```text
Note
Task
Link
Reminder
Idea
Meeting
Follow-up
```

### Status Options

```text
Inbox
Active
Waiting
Scheduled
Done
Archived
```

### Priority Options

```text
Low
Medium
High
Urgent
```

### Area Options

```text
Personal
SolQuim
GREQ
Mallitalytics
sophIA
Finance
Operations
Commercial
Admin
```

### Recommended Views

1. Today
2. Upcoming
3. Open Tasks
4. Read Later
5. Ideas
6. Meetings
7. Waiting For
8. GREQ
9. SolQuim
10. Mallitalytics

---

## 15. Integration Rules

### Rule 1: Calendar Owns Time

If an item has a specific time, it should usually go to Google Calendar.

Examples:

```text
5:30 PM
Tomorrow at 8 AM
Friday from 2 to 3
Next Monday at noon
```

Destination:

```text
Google Calendar
```

---

### Rule 2: Notion Owns Work

If an item is a task, idea, link, or note without a specific scheduled time, it should go to Notion.

Examples:

```text
Call supplier tomorrow
Save this article
Idea for new workflow
Review invoice process
```

Destination:

```text
Notion
```

---

### Rule 3: Database Owns Memory

Every command should be saved in the database regardless of destination.

This allows Kibo to answer questions later, such as:

```text
What did I save yesterday?
What tasks did I create this week?
Show me open GREQ follow-ups.
```

---

## 16. Notification Strategy

### Telegram Notifications

Used for:

- Immediate confirmations.
- Error messages.
- Daily summaries.
- Follow-up prompts.

### Google Calendar Notifications

Used for:

- Meetings.
- Timed reminders.
- Phone notifications.

### Email Notifications

Used for:

- Daily digest.
- Weekly review.
- Important missed tasks.

### Notion Notifications

Used for:

- Task due dates.
- Workspace review.

---

## 17. Error Handling

Kibo should never fail silently.

If an integration fails, Kibo should:

1. Save the command in the database.
2. Mark the action as failed.
3. Send a Telegram response explaining the issue.
4. Suggest the next step.

Example:

```text
I saved your command, but I could not create the Google Calendar event because your Google connection needs to be refreshed.
```

---

## 18. Security Requirements

Kibo will handle sensitive personal data, so security must be included from the start.

Requirements:

- Validate Telegram user ID.
- Support only authorized users during MVP.
- Encrypt OAuth tokens.
- Do not expose raw tokens in logs.
- Use environment variables for secrets.
- Store only required data.
- Allow data deletion.
- Use HTTPS webhooks.
- Use least-privilege permissions for Notion and Google.

---

## 19. Environment Variables

Suggested `.env` structure:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=
APP_ENV=development
APP_BASE_URL=
DATABASE_URL=
NOTION_API_KEY=
NOTION_INBOX_DATABASE_ID=
NOTION_TASKS_DATABASE_ID=
NOTION_LINKS_DATABASE_ID=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
GMAIL_SENDER_EMAIL=
OPENAI_API_KEY=
DEFAULT_TIMEZONE=America/Santo_Domingo
SECRET_KEY=
```

---

## 20. MVP Roadmap

### Phase 1: Foundation

Goal: Receive Telegram messages and log them.

Tasks:

- Create Telegram bot.
- Build FastAPI backend.
- Add webhook endpoint.
- Validate Telegram user.
- Save raw messages to database.
- Send confirmation response.

Success criteria:

- Kibo receives and responds to Telegram messages.
- All messages are logged.

---

### Phase 2: Notion Capture

Goal: Save notes, tasks, and links to Notion.

Tasks:

- Create Notion databases.
- Connect Notion API.
- Implement `/note`.
- Implement `/task`.
- Implement `/link`.
- Save external Notion page IDs in database.

Success criteria:

- User can create Notion records from Telegram.

---

### Phase 3: Google Calendar Events

Goal: Create calendar events and reminders.

Tasks:

- Configure Google OAuth.
- Connect Google Calendar API.
- Implement `/event`.
- Implement `/remind`.
- Add default notifications.
- Handle timezone correctly.

Success criteria:

- User can create calendar events from Telegram.
- User receives phone notifications from calendar.

---

### Phase 4: Summaries

Goal: Send daily and weekly summaries.

Tasks:

- Implement `/summary today`.
- Implement `/summary week`.
- Add optional scheduled daily digest.
- Add optional email digest.

Success criteria:

- User receives a clear summary of captured items.

---

### Phase 5: Natural Language

Goal: Remove the need for strict commands.

Tasks:

- Add LLM parser.
- Define JSON schema.
- Validate parsed output.
- Add confidence threshold.
- Add clarification flow.

Success criteria:

- Kibo correctly classifies natural messages with high reliability.

---

## 21. Future Features

### Personal Productivity Features

- Voice note transcription.
- Smart tags.
- Project detection.
- Recurring reminders.
- Inbox cleanup suggestions.
- Weekly review assistant.
- Search command: “What did I save about payroll?”

### Business Features

- Team command center.
- Shared Notion workspaces.
- Task assignment.
- CRM follow-ups.
- Payment reminders.
- Meeting follow-up generation.
- Sales pipeline updates.
- Company-specific workflows.

### Advanced AI Features

- Auto-prioritization.
- Smart scheduling.
- Context-aware reminders.
- Summary generation.
- Agentic Notion updates through MCP/CLI tooling.

---

## 22. Commercial Potential

Kibo can be offered in multiple ways:

### Personal SaaS

For individuals who want fast capture and structured productivity.

Possible pricing:

```text
Free: limited commands
Pro: $7-$12/month
```

### Team Productivity Tool

For small teams that need shared task capture and follow-up.

Possible pricing:

```text
Team: $29-$49/month
```

### Business Workflow Assistant

For companies needing custom workflows.

Possible pricing:

```text
Business: $99-$299/month
```

### Consulting + Implementation

For businesses that want custom versions connected to their own Notion, Google Workspace, CRM, or operations database.

This may be the fastest early monetization path.

---

## 23. Product Positioning

Do not position Kibo as just another chatbot.

Better positioning:

```text
Kibo is a Telegram command center that turns messages into structured actions.
```

Alternative:

```text
Kibo connects your daily messages to the apps where work actually happens.
```

Strongest simple pitch:

```text
Text Kibo. It organizes the work.
```

---

## 24. Success Metrics

### MVP Metrics

- Commands processed per day.
- Successful action creation rate.
- Failed command rate.
- Average response time.
- Number of notes/tasks/events created.
- Daily active users.
- Weekly active users.

### Product Metrics

- Activation rate.
- Retention after 7 days.
- Retention after 30 days.
- Paid conversion rate.
- Average commands per user.
- Most used command type.

### Quality Metrics

- Intent classification accuracy.
- Time extraction accuracy.
- User correction frequency.
- Integration failure frequency.

---

## 25. MVP Definition

The MVP is complete when a user can do the following from Telegram:

1. Save a note to Notion.
2. Create a task in Notion.
3. Save a link to Notion.
4. Create a reminder in Google Calendar.
5. Create a calendar event in Google Calendar.
6. Receive a confirmation message.
7. Retrieve a daily summary.
8. Have all commands stored in a database.

MVP success target:

```text
At least 90% success rate for structured commands.
```

---

## 26. Immediate Next Steps

### Step 1: Create the Notion workspace

Create these databases:

1. Kibo Command Inbox
2. Kibo Tasks
3. Kibo Read Later
4. Kibo Ideas
5. Kibo Logs

### Step 2: Create the Telegram bot

Use BotFather to create the bot and obtain the bot token.

### Step 3: Create the backend repository

Suggested structure:

```text
kibo/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   └── telegram.py
│   ├── services/
│   │   ├── parser.py
│   │   ├── notion_service.py
│   │   ├── calendar_service.py
│   │   └── email_service.py
│   ├── models/
│   │   └── schemas.py
│   └── db/
│       ├── database.py
│       └── models.py
├── tests/
├── .env.example
├── requirements.txt
├── README.md
└── render.yaml
```

### Step 4: Build structured command MVP

Start with:

```text
/note
/task
/link
```

Then add:

```text
/remind
/event
/summary
```

### Step 5: Add natural language parsing

Only after the command-based version works reliably.

---

## 27. Final Product Principle

Kibo should be simple at the surface and structured underneath.

User experience:

```text
Send a message.
```

System behavior:

```text
Classify → route → execute → confirm → archive.
```

That is the product.

