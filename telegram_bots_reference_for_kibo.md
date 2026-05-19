# Telegram Bots Reference for Kibo

Source: https://core.telegram.org/bots  
Retrieved for: Kibo app planning and implementation context

---

## 1. What Telegram Bots Are

Telegram bots are small applications that run entirely inside Telegram. Users interact with them through chat-based interfaces, buttons, inline actions, Mini Apps, and integrations.

For Kibo, this means Telegram can serve as the user-facing command center while the actual logic runs on Kibo's backend server.

**Kibo interpretation:**

```text
User sends command in Telegram
        ↓
Telegram forwards update to Kibo backend
        ↓
Kibo processes intent
        ↓
Kibo writes to Notion, Google Calendar, Gmail, or database
        ↓
Kibo confirms result back in Telegram
```

---

## 2. Strategic Importance for Kibo

Telegram's bot platform is free for both users and developers and hosts more than 10 million bots.

This makes Telegram a strong starting point for Kibo because:

- Users already understand chat interfaces.
- No custom mobile app is needed for the MVP.
- Telegram works well on iPhone, Android, desktop, and web.
- Bot interactions can support commands, AI chat, task routing, reminders, and workflow automation.
- Telegram can become the front door for external tools such as Notion, Google Calendar, Gmail, and future business systems.

---

## 3. What Bots Can Do

Telegram highlights several categories of bot capabilities. The most relevant ones for Kibo are listed below.

### 3.1 Replace Entire Websites

Telegram bots can host Mini Apps built with JavaScript. These Mini Apps can provide richer interfaces directly inside Telegram.

**Kibo use case:**

In the future, Kibo could include a Telegram Mini App for:

- Reviewing today's tasks
- Editing captured notes
- Seeing upcoming reminders
- Choosing destination database
- Managing settings
- Reviewing failed commands

For the MVP, a Mini App is not required. A chat-first experience is enough.

---

### 3.2 Integrate AI Chatbots

Telegram bots support threaded conversations, which can help AI chatbots manage multiple topics in parallel. Telegram also supports streaming live responses as they are generated.

**Kibo use case:**

This is highly relevant because Kibo is designed to interpret natural-language commands such as:

```text
Book meeting with Richard today from 5:30 to 6:30.
Remind me tomorrow at 8am to check the exchange rate.
Save this link for later.
Create a task to call Elayne about invoices.
```

The AI layer should classify each message into an intent:

```text
note
link
task
reminder
event
question
unknown
```

---

### 3.3 Manage Business Workflows

Telegram Business users can connect bots to process and answer messages on their behalf. Developers can enable Business Mode in BotFather if their bot supports Telegram Business integration.

**Kibo use case:**

This may become important in later versions if Kibo evolves from a personal assistant into a business operations assistant.

Possible future business workflows:

- Convert client messages into tasks
- Route sales follow-ups to Notion or CRM
- Create calendar events from operational conversations
- Generate daily business digests
- Capture payment reminders
- Create internal support tickets

For the MVP, Kibo should start as a personal bot, not a Telegram Business bot.

---

### 3.4 Create Custom Tools

Telegram bots can be created for specific tasks such as file conversion, chat management, information fetching, productivity workflows, and service integrations.

**Kibo use case:**

Kibo should be positioned as a custom productivity tool:

```text
Telegram command center → structured actions
```

Core tools:

- Create Notion task
- Save Notion note
- Save read-later link
- Create Google Calendar event
- Create Google Calendar reminder
- Send Gmail digest
- Log every command to database

---

### 3.5 Integrate with Services and Devices

Telegram bots and Mini Apps can integrate with third-party services, APIs, and devices.

**Kibo use case:**

Kibo's core value depends on integration quality.

Initial integrations:

- Notion API
- Google Calendar API
- Gmail API or SMTP
- PostgreSQL/Supabase database

Future integrations:

- Obsidian sync
- Google Drive
- Slack
- WhatsApp via external provider
- Airtable
- CRM tools
- Business dashboards

---

### 3.6 Monetize the Service

Telegram offers monetization mechanisms such as subscriptions, digital products, paid content, affiliate programs, and Telegram Stars.

**Kibo use case:**

Monetization should not be part of the MVP, but future commercial versions could include:

- Free personal tier
- Pro individual tier
- Business/team tier
- Custom workflow tier
- White-label assistant for small companies

---

## 4. How Telegram Bots Work

Telegram bots are special accounts that do not require a phone number. They are connected to the owner's server, which processes user input and sends responses back through the Telegram Bot API.

Telegram handles communication between users and bots. Developers communicate with Telegram through an HTTPS-based API known as the Bot API.

**Kibo technical interpretation:**

```text
Telegram user
   ↓
Telegram Bot Platform
   ↓
Kibo backend server
   ↓
Intent parser + action router
   ↓
External services
```

The backend is responsible for:

- Receiving Telegram updates
- Authenticating allowed users
- Parsing messages
- Classifying intent
- Calling external APIs
- Saving command logs
- Returning useful confirmations

---

## 5. Important Bot Limitations

Telegram bots differ from normal user accounts in several ways.

### 5.1 Bots Cannot Start Conversations

Bots cannot initiate a conversation with a user. The user must first message the bot, add it to a group, or open it through a `t.me` link.

**Kibo implication:**

The onboarding flow must ask the user to start the bot first.

Example:

```text
Open Telegram → Search @KiboBot → Press Start
```

Once the user has started the bot, Kibo can send confirmations, reminders, and follow-ups.

---

### 5.2 Bots Have Limited Cloud Storage

Telegram notes that bots have limited cloud storage and older messages may be removed after processing.

**Kibo implication:**

Telegram must not be treated as the source of truth.

Kibo needs its own storage layer:

```text
PostgreSQL / Supabase / SQLite
```

Every command should be stored with:

- Raw text
- Parsed intent
- Created action
- Destination app
- External record ID
- Timestamp
- User ID
- Status
- Error message, if any

---

### 5.3 Group Privacy Mode

By default, bots added to groups only receive relevant messages, depending on Privacy Mode settings.

**Kibo implication:**

For the first version, Kibo should operate in private chat only.

Later, group mode could support:

- Team command center
- Shared task capture
- Meeting notes
- Operational task routing

---

## 6. Bot Creation Process

Telegram bots are created through BotFather.

Basic setup flow:

```text
1. Open Telegram
2. Search for @BotFather
3. Create a new bot
4. Choose display name
5. Choose username
6. Receive bot token
7. Store token securely
8. Connect token to backend
```

Telegram warns that the bot token is a unique identifier and must be stored securely. Anyone with the token can control the bot.

**Kibo security requirements:**

- Never commit the bot token to GitHub.
- Store token in environment variables.
- Use secret managers in Render, Railway, Fly.io, or Vercel.
- Rotate token if exposed.
- Restrict bot usage to approved Telegram user IDs during MVP.

---

## 7. Recommended Kibo Bot Design

### 7.1 MVP Bot Behavior

Kibo should start with explicit commands:

```text
/note Idea for improving the dashboard
/task Call supplier tomorrow
/remind Check exchange rate tomorrow at 8am
/event Meeting with Richard today 5:30pm-6:30pm
/link https://example.com
```

Then move to natural language:

```text
Book meeting with Richard today from 5:30 to 6:30.
Remind me tomorrow at 8am to check Banco Popular.
Save this article for later: https://example.com
```

---

### 7.2 Supported Intents

| Intent | Description | Destination |
|---|---|---|
| `note` | General note or idea | Notion Inbox |
| `task` | Action item without fixed time block | Notion Tasks |
| `reminder` | Timed follow-up | Google Calendar or Notion reminder |
| `event` | Meeting or scheduled time block | Google Calendar |
| `link` | Read-later item | Notion Read Later |
| `digest` | Summary request | Database + Telegram response |
| `unknown` | Ambiguous message | Ask clarification |

---

### 7.3 Confirmation Style

Kibo should confirm actions clearly and briefly.

Examples:

```text
Saved to Notion Inbox: "Idea for improving the dashboard"
```

```text
Created calendar event: Meeting with Richard, today 5:30 PM–6:30 PM.
```

```text
Created task: Call supplier. Due tomorrow.
```

If uncertain:

```text
I found a task but no due date. Save it without a due date?
```

---

## 8. Backend Requirements

### 8.1 Core Backend Modules

```text
app/
├── main.py
├── config.py
├── telegram/
│   ├── webhook.py
│   ├── handlers.py
│   └── responses.py
├── parser/
│   ├── intent_classifier.py
│   ├── date_parser.py
│   └── schemas.py
├── integrations/
│   ├── notion_client.py
│   ├── google_calendar_client.py
│   ├── gmail_client.py
│   └── telegram_client.py
├── database/
│   ├── models.py
│   ├── repository.py
│   └── migrations/
└── services/
    ├── command_router.py
    ├── reminder_service.py
    └── digest_service.py
```

---

### 8.2 Environment Variables

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=
NOTION_API_KEY=
NOTION_INBOX_DATABASE_ID=
NOTION_TASKS_DATABASE_ID=
NOTION_LINKS_DATABASE_ID=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
DATABASE_URL=
OPENAI_API_KEY=
APP_ENV=development
```

---

### 8.3 Database Tables

#### `commands`

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Internal command ID |
| `telegram_user_id` | Text | Telegram user identifier |
| `raw_text` | Text | Original user message |
| `intent` | Text | Parsed command type |
| `status` | Text | success, failed, pending, clarification_needed |
| `destination` | Text | Notion, Calendar, Gmail, etc. |
| `external_id` | Text | ID from external app |
| `created_at` | Timestamp | Capture time |
| `processed_at` | Timestamp | Processing time |
| `error_message` | Text | Failure details |

#### `users`

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Internal user ID |
| `telegram_user_id` | Text | Telegram account |
| `name` | Text | User name |
| `timezone` | Text | User timezone |
| `notion_workspace_id` | Text | Connected Notion workspace |
| `google_account_email` | Text | Connected Google account |
| `created_at` | Timestamp | Signup date |

---

## 9. Kibo MVP Scope

### Must Have

- Telegram bot setup through BotFather
- Cloud backend receiving Telegram messages
- User allowlist for security
- Structured command parsing
- Notion task creation
- Notion note creation
- Notion link saving
- Google Calendar event creation
- Google Calendar reminder creation
- Command logging
- Telegram confirmation messages

### Should Have

- Natural-language parsing
- Error handling
- Timezone support
- Daily digest command
- Basic admin logs
- Retry failed commands

### Nice to Have Later

- Telegram Mini App
- Voice note transcription
- Image/screenshot capture
- Obsidian sync
- Team workspaces
- Billing
- Business templates
- WhatsApp support

---

## 10. Development Roadmap

### Phase 1: Private MVP

Goal: Make Kibo useful for one user.

Deliverables:

- Telegram bot
- FastAPI backend
- Notion integration
- Google Calendar integration
- Command log database
- Basic `/note`, `/task`, `/link`, `/event`, `/remind` commands

Success criteria:

- Commands succeed reliably.
- User can capture from iPhone.
- Notion receives structured records.
- Calendar events are created correctly.
- Telegram confirms each action.

---

### Phase 2: Natural Language Layer

Goal: Remove rigid command syntax.

Deliverables:

- Intent classifier
- Date/time parser
- Confirmation workflow for uncertain commands
- Smart tags and areas
- Better error messages

Success criteria:

- Kibo correctly classifies most normal user messages.
- User only needs to clarify when truly necessary.

---

### Phase 3: Productization

Goal: Prepare Kibo for external users.

Deliverables:

- Landing page
- User onboarding
- OAuth connection flow
- Multi-user database design
- Usage limits
- Privacy policy
- Terms of service
- Admin panel

Success criteria:

- A new user can connect Telegram, Notion, and Google Calendar without manual developer setup.

---

### Phase 4: Business Assistant

Goal: Turn Kibo into a team/business workflow assistant.

Deliverables:

- Shared team inbox
- Role-based permissions
- Business templates
- Internal task assignment
- Email digests
- Operations dashboard
- Optional Telegram Business support

Success criteria:

- Small teams can use Kibo to route operational tasks and reminders.

---

## 11. Key Product Principles

1. Telegram is the command center, not the database.
2. Notion is the structured productivity workspace.
3. Google Calendar handles scheduled time.
4. The backend keeps the audit trail.
5. Kibo should ask for clarification only when necessary.
6. Every command should end with confirmation.
7. The MVP should be reliable before it is smart.
8. Security matters because integrations expose personal and business data.

---

## 12. Implementation Notes

Telegram is a good foundation for Kibo because it provides:

- A familiar chat interface
- Bot accounts without phone numbers
- HTTPS-based Bot API
- Mobile and desktop access
- Support for AI chat workflows
- Mini App expansion path
- Business integration path
- Monetization expansion path

For Kibo, the immediate goal should be:

```text
Telegram message → parsed intent → action in Notion or Calendar → confirmation
```

The long-term vision is:

```text
A personal and business command center that turns messages into structured action.
```

---

## 13. Source Notes

This document is based on the official Telegram Bots introduction page:

https://core.telegram.org/bots

Important linked Telegram resources from that page:

- Detailed Guide to Bot Features
- Full Bot API Reference for Developers
- Basic Tutorial: From BotFather to Hello World
- Code Examples
- Telegram Mini Apps
- Telegram Business
- Telegram Payments and Stars

