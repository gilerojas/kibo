# Notion CLI (`ntn`) — Technical Overview & Reference

**Document type:** Tool review and reference context for AI agents
**Subject:** `ntn`, the official Notion command-line interface
**Last researched:** May 18, 2026
**Maintainer of tool:** Notion (`@makenotion`)
**Status:** Actively developed; described by Notion as early/alpha-stage during initial rollout, with authentication and platform support maturing over 2026

---

## 1. Executive Summary

`ntn` is Notion's official command-line interface, purpose-built for developers and AI coding agents to interact with Notion programmatically from a terminal rather than the Notion application UI. It consolidates three primary capabilities into a single binary: authenticated access to the full public Notion API, lifecycle management of **Notion Workers** (deployable TypeScript programs that extend Notion with syncs, tools, and webhooks), and file uploads. It was released as part of the **Notion Developer Platform** announcement in 2026 and ships alongside an official Agent Skill so coding agents can operate it without memorized syntax.

The tool is explicitly designed to be *self-documenting* and *agent-friendly*: every command exposes structured help, the API surface is discoverable from the terminal, and the inline request syntax is modeled on HTTPie. For AI agents, the operative principle is to query the CLI for syntax and schemas at runtime rather than relying on training data, because the API and command surface evolve.

---

## 2. Primary Purpose

`ntn` exists to turn Notion into a programmable surface accessible from the command line and from agent execution environments. Its three core purposes are:

1. **API access** — Make authenticated requests against any public Notion API endpoint (`/v1/...`) without configuring a separate HTTP client. The CLI injects `Authorization` and `Notion-Version` headers automatically.
2. **Workers management** — Scaffold, deploy, operate, and debug Notion Workers, which run on Notion's infrastructure and provide deterministic logic (data syncs, custom agent tools, webhook handlers) that LLM reasoning alone cannot reliably deliver.
3. **File operations** — Upload local files or register external file URLs (images, PDFs, static assets) for reference inside Notion pages.

It is positioned as an optional developer tool. End users of Notion do not need it; it targets developer workflows, CI pipelines, scripting, and autonomous agents.

---

## 3. Installation

### 3.1 Recommended: install script

```bash
curl -fsSL https://ntn.dev | bash
```

### 3.2 Alternative: npm

```bash
npm install --global ntn
# or, to pin the latest explicitly
npm install -g ntn@latest
```

The npm path requires **Node.js 22+** and **npm 10+**.

### 3.3 Verify installation

```bash
ntn --version
```

### 3.4 Shell completions

Tab completion (including API path and method suggestions) is supported for multiple shells:

```bash
ntn completions bash   # or: fish, zsh, powershell, elvish
```

### 3.5 Building from source

The CLI source is on GitHub at `makenotion/cli`. A local debug binary (installed as `ntnd`) can be built with [mise](https://mise.jdx.dev/):

```bash
git clone https://github.com/makenotion/cli.git
cd cli
mise build
```

### 3.6 Platform support

| Platform | Supported |
| --- | --- |
| macOS (x64, arm64) | Yes |
| Linux (x64, arm64) | Yes |
| Windows (native) | Not yet — "coming soon" as of May 2026; use WSL2 in the interim |

> **Agent note:** When running on Windows, prefer WSL2, or fall back to direct HTTP requests (`curl`) against the Notion API. In MSYS-based shells (Git Bash, MSYS2), leading-slash arguments may be rewritten to Windows paths, breaking API path arguments — pass paths without the leading slash, or use PowerShell/cmd.

---

## 4. Authentication

`ntn` supports two authentication models. Understanding which one applies to which command group is critical for agents.

### 4.1 Interactive login (OAuth, workspace-scoped)

```bash
ntn login
```

This opens a browser to an authorization page. The user must confirm that the verification code shown in the browser matches the code printed in the terminal before approving (this prevents a third party from completing the login). The resulting **workspace-scoped token** is stored in the OS credential store.

- Requires **full workspace membership**. Guests and restricted members cannot log in via the CLI; an admin must upgrade the role.
- Supports multiple workspaces; the interactive picker switches the default or adds a new workspace.

**Headless / CI login fallback:** On machines that cannot open a browser, `ntn login` prints a URL, a verification code, and a `ntn login poll` command. The user authorizes in any browser, then `ntn login poll` redeems the token on the original machine. Sessions expire after a short window. For unattended use, a personal access token is preferred over this flow.

```bash
ntn logout   # clears cached workspaces and deletes their tokens from the keychain
```

### 4.2 Personal access token / integration token (unattended)

For scripts, CI, and agents, export a token as an environment variable:

```bash
export NOTION_API_TOKEN=ntn_xxx...
ntn api v1/users/me
```

`NOTION_API_TOKEN` **takes precedence over the keychain entry**, so a single shell can mix `ntn login`-based commands and token-based commands depending on what is exported.

> **Important historical nuance for agents:** During the early alpha (≈ Q1 2026), community reports and the bundled Agent Skill stated that `ntn login` authenticated only `ntn workers`/`ntn tokens`, and that `ntn api` and `ntn files` required `NOTION_API_TOKEN`. The current official documentation (May 2026) states the keychain credential and `NOTION_API_TOKEN` are interchangeable across command groups, with the env var taking precedence. **Operationally safest default for agents:** check whether `NOTION_API_TOKEN` is set and use it if present; only fall back to `ntn login` when it is not. This avoids depending on auth behavior that has shifted between releases.

### 4.3 Credential storage and key environment variables

Tokens are stored in the OS credential store (Keychain on macOS, Secret Service on Linux) under service name `notion-cli`, keyed by workspace ID. Two non-secret files sit in the config directory: `config.json` (CLI version, default workspace, keyring toggle) and `workspaces.json` (cached workspace IDs/names). The config directory resolves to `NOTION_HOME`, else `$XDG_CONFIG_HOME/notion`, `$HOME/.config/notion`, or `$HOME/.notion`.

| Variable | Purpose |
| --- | --- |
| `NOTION_API_TOKEN` | API token; overrides keychain. Required for unattended use. |
| `NOTION_WORKSPACE_ID` | Target a non-default workspace for a single command without switching defaults. |
| `NOTION_KEYRING` | Set to `0` to store tokens in plaintext `auth.json` instead of the OS keychain (for Docker, CI, SSH sessions without a usable keychain). |
| `NOTION_HOME` | Override the config directory. |
| `NOTION_API_VERSION` | Pin the `Notion-Version` header for a session/script. |
| `NOTION_WORKERS_CONFIG_FILE` | Path to `workers.json` (same as `--workers-config-file`). |

Opting out of the keychain (common in containers/CI):

```bash
NOTION_KEYRING=0 ntn login
```

### 4.4 Session inspection

```bash
ntn doctor   # reports on auth, keychain, network, and config health
```

---

## 5. Core Capabilities & Command Surface

`ntn` organizes commands into noun-verb groups. The following is a structured reference.

### 5.1 Global flags (available on every command)

| Flag | Description |
| --- | --- |
| `-v, --verbose` | Full error details, including request/response metadata to stderr (`Authorization` redacted). |
| `--workers-config-file <path>` | Path to a `workers.json` (overrides default lookup; its `workspaceId` selects the workspace). |
| `-V, --version` | Print version. |
| `-h, --help` | Print help for any command or subcommand. |

### 5.2 Authentication commands

| Command | Description |
| --- | --- |
| `ntn login` | Log in and connect to a workspace. |
| `ntn logout` | Clear stored credentials for the current workspace. |

### 5.3 API requests — `ntn api`

| Command | Description |
| --- | --- |
| `ntn api <path>` | Make an authenticated Notion API request. |
| `ntn api ls` | List all available API endpoints (add `--json` for scripting). |
| `ntn api <path> --help` | Show methods, doc links, and usage for an endpoint. |
| `ntn api <path> --spec [-X METHOD]` | Print a reduced OpenAPI fragment (request/response schema). |
| `ntn api <path> --docs [-X METHOD]` | Print the official markdown reference page for an endpoint. |

> If a path supports multiple methods, pass `-X` so `--spec`/`--docs` know which operation to inspect.

### 5.4 Pages — `ntn pages`

| Command | Description |
| --- | --- |
| `ntn pages get <page-id>` | Retrieve a page **as Markdown** (`--json` for raw JSON). Primary way to read page content. |
| `ntn pages create` | Create a page from Markdown. Flags: `--parent <page:ID\|database:ID\|data-source:ID>`, `--content <markdown>` (reads stdin if omitted). |
| `ntn pages update <page-id>` | Update page content from Markdown. `--allow-deleting-content` permits removing child pages/databases. |
| `ntn pages trash <page-id>` | Trash a page (`--yes` skips confirmation). |

### 5.5 Data sources — `ntn datasources`

In current API versions, what users call "databases" are exposed as **data sources**.

| Command | Description |
| --- | --- |
| `ntn datasources query <data-source-id>` | Query pages in a data source. Flags: `--limit <n>` (default **25**), `--start-cursor <cursor>`, `-s/--sort "<property> [asc\|desc]"` (repeatable), `--filter <json>`, `--filter-file <path\|->`. |
| `ntn datasources resolve <database-id>` | Resolve a database ID to its data source ID(s). |

### 5.6 Files — `ntn files`

| Command | Description |
| --- | --- |
| `ntn files create` | Upload a file (`< file.png` from stdin) or register an external URL (`--external-url <url>`). Quiet on success; progress bar only when stderr is a TTY. |
| `ntn files get <upload-id>` | Get upload details. |
| `ntn files list` | List file uploads. |

### 5.7 Workers — `ntn workers`

Workers are small TypeScript programs deployed to Notion's infrastructure. Worker ID resolves from `--worker-id`, then `workers.json` in the current directory.

| Command | Description |
| --- | --- |
| `ntn workers new [dir]` | Scaffold a project. Flags: `--force`, `--git/--no-git`, `--install/--no-install`. |
| `ntn workers deploy` | Build and upload. `--name <name>` required when creating; `--local-build` builds locally. |
| `ntn workers list` (`ls`) | List workers in the active workspace. |
| `ntn workers get [id]` | Show details for a worker. |
| `ntn workers create` | Create a worker without deploying code (`--name`). |
| `ntn workers delete [id]` (`rm`) | Delete a worker (`--yes`). |
| `ntn workers exec <key>` | Run a capability. Flags: `-d/--data <json>` (stdin if omitted), `--stream`, `-l/--local`, `--dotenv <path>`, `--no-dotenv`. |
| `ntn workers capabilities list` | List deployed capabilities. |
| `ntn workers tui` (`ui`) | Interactive terminal UI for managing workers. |

Common worker output flags: `--json` and `--plain` (mutually exclusive).

**Worker subgroups:**

| Subgroup | Key commands |
| --- | --- |
| `workers sync` | `status`, `trigger <key>` (`--preview`, `--context`), `pause`, `resume`, `state get`, `state reset` |
| `workers env` | `set <KEY=VALUE>`, `list`, `unset`, `pull`, `push` (values write-only; never returned by `list`) |
| `workers oauth` | `start <key>`, `token <key>`, `show-redirect-url` |
| `workers runs` | `list`, `logs <run-id>` |
| `workers webhooks` | `list [worker-id]` (prints generated webhook URLs — treat as secrets) |

### 5.8 Tokens — `ntn tokens`

Manages tokens used by `ntn workers`. Requires `ntn login`. Distinct from `NOTION_API_TOKEN` integration tokens.

```bash
ntn tokens create
ntn tokens ls
ntn tokens revoke <token-id>
```

### 5.9 Diagnostics

| Command | Description |
| --- | --- |
| `ntn doctor` | Check health of auth, keychain, network, and config. |
| `ntn update` | Update `ntn` to the latest version (`--force` to reinstall). |

---

## 6. The `ntn api` Inline Request Syntax

This is the most important section for agents that need to construct API calls. The syntax is inspired by HTTPie and implemented via `httpcliparser`.

### 6.1 Method inference

- No body → `GET`.
- Any inline body field, `--data`, or stdin JSON present → `POST`.
- Override with `-X METHOD` (e.g., `PATCH`, `DELETE`).

### 6.2 Inline input forms

| Form | Meaning | Example |
| --- | --- | --- |
| `path=value` | Body field, **string** value | `parent[page_id]=abc123` |
| `path:=json` | Body field, value keeps its **JSON type** | `archived:=true` |
| `name==value` | Query parameter | `page_size==100` |
| `Header:Value` | Request header | `Accept:application/json` |

`=` produces strings. `:=` produces typed JSON (booleans, numbers, arrays, objects, `null`).

### 6.3 Examples

```bash
# GET (no body)
ntn api v1/users/$USER_ID
ntn api v1/pages/$PAGE_ID

# POST with inline body fields (nested via bracket or dot notation)
ntn api v1/pages \
  parent[page_id]="$PARENT_PAGE_ID" \
  properties[Name][title][0][text][content]="CLI-created page"

# PATCH with typed assignment
ntn api "v1/pages/$PAGE_ID" -X PATCH \
  archived:=false \
  properties[Priority][number]:=2

# Append blocks, preserving array order with explicit indexes
ntn api "v1/blocks/$PAGE_ID/children" -X PATCH \
  children[0][type]=paragraph \
  children[0][paragraph][rich_text][0][text][content]="First paragraph"

# Repeated values appended in input order with []
ntn api v1/comments \
  parent[page_id]="$PAGE_ID" \
  rich_text[][text][content]="First line" \
  rich_text[][text][content]="Second line"

# JSON body via stdin, file, or --data (use only ONE body source per request)
ntn api v1/pages < create-page.json
ntn api v1/search --data '{"query":"roadmap","page_size":10}'
jq -n --arg p "$PARENT" '{parent:{page_id:$p},properties:{title:{title:[{text:{content:"Generated"}}]}}}' | ntn api v1/pages

# Pin API version for one request or a session
ntn api v1/users/me --notion-version 2026-03-11
export NOTION_API_VERSION=2026-03-11
```

> Use bracket notation for property names containing spaces or punctuation: `properties[Build version][rich_text][0][text][content]="2026.05.11"`.

### 6.4 Debugging requests

```bash
ntn --verbose api v1/pages/$PAGE_ID
```

Verbose prints final method, URL, request headers, JSON body, response status/headers/body to stderr. `Authorization` is redacted by default. A hidden `--unsafe-verbose` flag disables redaction and can leak the bearer token — never use it outside a controlled local environment, and never paste its output anywhere shared.

---

## 7. Agent-Specific Operating Guidance

This section is the operational core for AI agents tasked with using `ntn`.

### 7.1 Treat the CLI as the source of truth, not training data

The CLI is self-documenting and the API surface changes. **Always prefer runtime discovery over memorized syntax:**

- `ntn api ls` — enumerate every public endpoint.
- `ntn api <path> --spec [-X METHOD]` — fetch the request/response schema.
- `ntn api <path> --docs [-X METHOD]` — fetch the official endpoint documentation.
- `ntn <command> --help` — usage for any command/subcommand.

### 7.2 Canonical workflow pattern

The dominant agent pattern is **Search → Resolve/Fetch → Act**:

1. Locate the target (search or list).
2. Resolve identifiers. Database IDs are not data source IDs — use `ntn datasources resolve <database-id>` to obtain the `data_source_id` before querying or creating entries.
3. Perform the operation (`pages create`, `datasources query`, `api ...`).

### 7.3 ID-type discipline

Notion exposes several ID types that are not interchangeable: `page_id`, `database_id`, `data_source_id`, and view URLs. "Page not found" / "could not find page with ID" errors are very frequently an ID-type mismatch (e.g., passing a database ID where a data source ID is required), not a permissions issue. Resolve IDs explicitly before acting.

### 7.4 Output handling

- `ntn pages get` returns Markdown by default — convenient for reading; add `--json` when structured fields are needed.
- Worker commands support `--json` and `--plain` for machine parsing.
- `ntn files create` is intentionally silent on success.
- When piping API output, parse JSON structurally (e.g., `jq`) rather than with regex.

### 7.5 Prefer the env-token path for unattended runs

Check `NOTION_API_TOKEN` first; use it if set. Only invoke the interactive `ntn login` flow when no token is available and a human can complete the browser step.

---

## 8. Integration with the Notion API & Existing Workflows

- **Header management:** `ntn api` sets `Authorization` and the required `Notion-Version` header automatically (HTTP clients hitting the API directly must send `Notion-Version` explicitly, e.g., `2025-09-03` or later).
- **Rate limits:** The Notion API enforces roughly **3 requests/second** on average. The CLI does not bypass this; agents should pace bulk operations and handle pagination via `--start-cursor` / cursor fields.
- **Sharing requirement:** Integration tokens only see pages/databases explicitly shared with the integration. An unshared page returns **404** even though it exists. Confirm the human's own access first — if they cannot open the resource in Notion, the CLI cannot either.
- **API limitations inherited from Notion:** Database *view filters* are UI-only and cannot be set via the API. Inline data sources can be created with `"is_inline": true`.
- **Workers as the deep-integration path:** For deterministic logic (nightly syncs, custom agent tools, webhook handlers), Workers run on Notion infrastructure at a fraction of the token cost of LLM reasoning and are more reliable. `ntn` is the deployment and operations tool for them.
- **Relationship to Notion MCP:** Notion also ships a Remote MCP server (`https://mcp.notion.com/mcp`) offering OAuth-scoped, workspace-wide access with capabilities `ntn` does not expose (cross-source AI search across Slack/Drive, view creation, database view queries). The CLI and MCP are complementary; for one-shot scripted/agent tasks the CLI path is typically sufficient and more context-efficient, while MCP suits interactive, full-workspace sessions.
- **Bundled Agent Skill:** Notion publishes an official skill at `makenotion/skills` (`skills/notion-cli/SKILL.md`), installable into agent environments (e.g., `npx skills add https://github.com/makenotion/skills --skill notion-cli`). It encodes the discovery-first principle and is recommended context for any agent operating `ntn`.

---

## 9. Limitations, Known Issues & Prerequisites

### Prerequisites

- macOS or Linux (or WSL2 on Windows); Node.js 22+/npm 10+ for the npm install path.
- Full workspace membership for `ntn login`; an integration token shared with target resources for `ntn api`/`ntn files`.
- A usable OS keychain, **or** `NOTION_KEYRING=0` for containers/CI/SSH.

### Limitations & known issues

- **No native Windows binary** as of May 2026; MSYS shells mangle leading-slash path arguments.
- **Auth model has shifted between releases.** Notion characterized early auth as "alpha-y." Do not hard-code assumptions about which auth applies to which command group; detect `NOTION_API_TOKEN` and prefer it.
- **Thin REST wrapper, not full Notion surface.** `ntn api` calls `/v1/` REST endpoints. Relative to Remote MCP it lacks cross-workspace AI search (title search only), view create/update, and database view queries. It does, however, offer direct block operations and file upload that MCP does not.
- **Inherited API constraints:** ~3 req/s rate limit, integration-must-be-shared (404 otherwise), UI-only database view filters.
- **Body-source exclusivity:** Only one of inline fields, `--data`, or stdin JSON per request; mixing them is an error.
- **CLI source repository** was not public during the initial alpha period; agents should rely on the live docs and the self-documenting commands rather than the repository.

---

## 10. Review — Bottom Line

`ntn` is a competent, well-scoped first-party tool that does exactly what a CLI in the agent era should: structured help, runtime-discoverable schemas, HTTPie-style inline request construction, and an official bundled skill so agents do not guess. Its standout value is **Workers** — the only first-party path to deploy deterministic logic onto Notion's infrastructure — together with frictionless file uploads and clean Markdown page reads.

The honest caveats: it is a relatively young tool whose authentication behavior has visibly evolved between releases, it lacks native Windows support, and as a thin REST wrapper it is less capable than Notion's Remote MCP for workspace-wide search and view manipulation. For scripted automation, CI, and coding agents on macOS/Linux that need API access, file uploads, or Workers, `ntn` is the right default. Teams needing OAuth-scoped, workspace-wide interactive access — or Windows-native tooling today — should pair it with (or substitute) Notion MCP or direct HTTP calls. Choose `ntn` when you want a first-party tool, OAuth login, or you are building Workers; reach for MCP when you need full-workspace reach inside an interactive session.

---

## 11. Sources

- Notion CLI — Overview (official): https://developers.notion.com/cli/get-started/overview
- Notion CLI — Installation (official): https://developers.notion.com/cli/get-started/installation
- Notion CLI — Authentication (official): https://developers.notion.com/cli/get-started/authentication
- Notion CLI — API requests guide (official): https://developers.notion.com/cli/guides/api-requests
- Notion CLI — Command reference (official): https://developers.notion.com/cli/reference/commands
- Notion Help Center — "Use Notion from your terminal with Notion CLI": https://www.notion.com/help/use-notion-from-your-terminal-with-notion-cli
- Notion Developer Platform release notes (May 13, 2026): https://www.notion.com/releases/2026-05-13
- Official Agent Skill — `makenotion/skills` (`skills/notion-cli/SKILL.md`): https://github.com/makenotion/skills/blob/main/skills/notion-cli/SKILL.md
- Third-party critical analysis — Sakasegawa, "I Built a Coding-Agent-Friendly CLI for Every Notion User" (Mar 19, 2026): https://nyosegawa.com/en/posts/notion-cli-for-coding-agent/
- npm package: https://www.npmjs.com/package/ntn

> **Note on conflicting sources:** Official docs (May 2026) and the bundled Skill / third-party analysis (Q1 2026) disagree on whether `ntn login` authenticates `ntn api`/`ntn files`. This document treats the current official behavior as authoritative while flagging the discrepancy, because the auth model demonstrably changed during the alpha period. Agents should detect `NOTION_API_TOKEN` at runtime rather than depend on either claim.
