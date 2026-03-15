## MCP Apps

MCP Apps are interactive HTML interfaces served directly inside AI conversations. Instead of text-only responses, your AI agent can render visual dashboards, photo grids, control panels, and forms.

:::info Client Support
MCP Apps require an MCP client that supports HTML rendering. Currently, **Claude Desktop** and **Codex** display them natively. Other clients (Claude Code, Cursor, Copilot CLI) receive text-only fallbacks.
:::

### How It Works

When a service adapter implements app support, it returns HTML alongside tool results. The MCP client renders this HTML inline in the conversation. Apps can include CSS for styling and JavaScript for interactivity.

Apps are read-only previews by default. They display data from your services but don't modify state (modifications happen through regular tool calls in the conversation).

### Available Apps

| Service | App | What It Shows |
|---------|-----|---------------|
| Home Assistant | Entity dashboard | Device states, sensor readings, toggle switches |
| Immich | Photo grid | Album thumbnails, search results with image previews |
| Paperless-ngx | Document search | Document previews with metadata and tags |
| Uptime Kuma | Status dashboard | Monitor status indicators, uptime percentages |
| Forgejo | Repo browser | Repository file trees, issue lists |

### Self-MCP Apps

When [Self-MCP](self-mcp) is enabled, three management apps are also available:

- **Dashboard** (`mcp_home_ui_dashboard`) — Visual overview of all connected services and their health
- **Service Control** (`mcp_home_ui_service_control`) — Manage service connections
- **Config Viewer** (`mcp_home_ui_config`) — View system configuration

### Building Custom Apps

Service adapters can provide apps by implementing the `IAppProvider` interface. See [Developer Resources](developer) for the adapter structure and interface details.
