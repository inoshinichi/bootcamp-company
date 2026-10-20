# MCP Integration Guide

> **Updated 2026-10**: Mail, calendar, files and Slack should first be connected through Claude's official connectors (claude.ai → Connectors). Mail on rental servers, iPhone calendars, etc. use the read-only tools bundled in the plugin (`references/connections.md`). The methods below are only for services not covered by official connectors.


cc-company works with MCP (Model Context Protocol) servers. Setting up MCP servers allows the secretary to directly operate external services.

## How It Works

No special configuration is needed on the cc-company side. Just add MCP servers to Claude Code, and the secretary will automatically use them.

```
You: Schedule a meeting with Company A tomorrow at 2pm

Secretary: Added to your calendar!
           I've also added "Prepare meeting materials for Company A" to your TODOs.
```

## Recommended MCP Servers

### Notion (Official)

Connect with your knowledge base and databases. The secretary can read and update Notion pages.

**Method 1: OAuth (Recommended)**

```bash
claude mcp add-json --scope user notion '{"type":"http","url":"https://mcp.notion.com/mcp"}'
```

After running, OAuth authentication opens in your browser. No manual API key setup needed.

**Method 2: API Token**

```bash
claude mcp add --scope user notion -e NOTION_TOKEN=ntn_YOUR_TOKEN -- npx -y @notionhq/notion-mcp-server
```

Create an API token at [Notion Integrations](https://www.notion.so/my-integrations).

**Capabilities:**
- Read, create, and update Notion pages
- Search and update databases
- Secretary can reference your existing knowledge base

---

### Google Calendar (fallback)

> Normally not needed: connect Google Calendar with the one-click Claude connector instead. This is a fallback only for when the connector cannot be used (it needs a Google Cloud key and is hard for beginners).

Schedule management. The secretary can register meetings and set reminders.

```bash
claude mcp add --scope user google-calendar \
  -e GOOGLE_OAUTH_CREDENTIALS=/path/to/gcp-oauth.keys.json \
  -- npx -y @cocal/google-calendar-mcp
```

**Prerequisites:**
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Calendar API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials JSON

**Capabilities:**
- Create, view, modify, and delete events
- Show today's/this week's schedule
- Check availability
- Manage recurring events

---

### GitHub (Official)

Repository management. Great synergy with the Engineering department.

**Method 1: HTTP (Recommended)**

```bash
claude mcp add-json --scope user github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer YOUR_GITHUB_PAT"}}'
```

**Method 2: Docker**

```bash
claude mcp add --scope user github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_PAT \
  -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

Create a token at [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens).

**Capabilities:**
- Create, view, and search issues
- Manage and review PRs
- Check repository status
- Code search

---

### Slack (Official)

Team communication. Works well with Sales and PM departments.

**Method 1: OAuth (Recommended)**

```bash
claude mcp add-json --scope user slack '{"type":"http","url":"https://mcp.slack.com/mcp","oauth":{"clientId":"1601185624273.8899143856786","callbackPort":3118}}'
```

After running, Slack OAuth authentication opens in your browser.

**Method 2: Install as plugin**

```bash
claude plugin install slack
```

**Capabilities:**
- Send and check messages
- Monitor channel activity
- Look up user info
- Client communication reminders

::: warning Note
Your workspace admin must have approved MCP integration.
:::

---

## Setup Methods

### Via Command (Recommended)

Just run the `claude mcp add` commands above. Restart Claude Code after setup.
`--scope user` makes the server available in every folder. Without it, the default scope is `local` (only the folder you were in).

### Where the settings live

MCP servers are not stored in `~/.claude/settings.json`.

- **User and local scope:** `~/.claude.json` (written by `claude mcp add`; no need to edit by hand)
- **Project scope (`--scope project`, shared in the folder):** `.mcp.json`

```json
{
  "mcpServers": {
    "notion": {
      "type": "http",
      "url": "https://mcp.notion.com/mcp"
    }
  }
}
```

(Example of `.mcp.json`.)

---

## Examples with the Secretary

Once MCP servers are set up, the secretary uses them naturally.

```
> What's my schedule this week?
Secretary: Let me check your calendar.
      - Monday 10:00 Weekly meeting with Company A
      - Wednesday 14:00 Hearing with Company B
      - Friday All day Tax filing deadline
      Is the proposal for Company B on Wednesday ready?

> Summarize the meeting notes with Company A in Notion
Secretary: Done. Created a meeting notes page in Notion.
           I've also saved a summary in secretary/notes/.

> Create an issue for this bug
Secretary: Created an issue on GitHub.
           I've also logged it in engineering/debug-log/.
```

## Works Without MCP Too

cc-company works perfectly fine without any MCP servers. The secretary functions fully with just file management within `.company/`.

MCP is a "nice to have" option.
