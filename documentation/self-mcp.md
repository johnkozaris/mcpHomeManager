## Self-MCP

When self-MCP is enabled, your AI agent can manage MCP Home Manager itself through additional MCP tools. You can ask your AI agent to connect services, toggle tools, check health, and review audit logs — all without opening the web UI.

### Dynamic Server Instructions

The gateway automatically tells your AI agent what services are connected and what each one does. When services change, the instructions update to reflect the current state. Your agent always has context about what's available — no manual prompting needed.

### Enabling Self-MCP

The primary way to control self-MCP is the toggle switch in **Settings > Security** (admin only). Non-admin users see a badge showing the current state but cannot change it.

As a fallback, you can set `SELF_MCP_ENABLED=false` in your `.env` file to disable it globally, overriding the UI setting.

### Available Self-Management Tools

:::tools
- `mcp_home_list_services` — List all connected services with health status and tool counts
- `mcp_home_add_service` — Connect a new service (type, URL, credentials)
- `mcp_home_update_service` — Update an existing service connection (URL, credentials, display name, enabled state)
- `mcp_home_delete_service` — Permanently delete a service connection and all its tools
- `mcp_home_toggle_tool` — Enable or disable a specific tool
- `mcp_home_list_tools` — List all available tools across all services
- `mcp_home_health` — Check overall system health
- `mcp_home_get_logs` — Query the audit log (filter by user, service, time range)
- `mcp_home_add_generic_tool` — Define a new custom tool on any service
- `mcp_home_update_generic_tool` — Modify an existing custom tool definition
- `mcp_home_delete_generic_tool` — Remove a custom tool
:::

### Interactive UI Apps

When supported by your MCP client (e.g., Claude Desktop), self-MCP also exposes interactive HTML dashboards:

- `mcp_home_ui_dashboard` — Visual overview of services and health
- `mcp_home_ui_service_control` — Manage service connections
- `mcp_home_ui_config` — System configuration viewer

### Restart Note

New tools register immediately on the MCP endpoint. However, Claude Code, Cursor, and Copilot cache the tool list at startup. After connecting, updating, or removing services, restart these clients to pick up the changes.

### Example Conversation

Here is a realistic exchange showing self-MCP in action:

**You:** "Add my Nextcloud server at https://cloud.example.com with app password user:xxxxx-xxxxx"

**AI Agent:** *Calls `mcp_home_add_service` with type "nextcloud", URL "https://cloud.example.com", credentials "user:xxxxx-xxxxx"*

"Done! I've connected your Nextcloud server. The connection tested successfully — 5 tools are now available."

**You:** "What tools do I have now?"

**AI Agent:** *Calls `mcp_home_list_tools`*

"You have 15 tools across 3 services: Home Assistant (4 tools), Paperless-ngx (5 tools), and Nextcloud (5 tools, just added). All tools are enabled."

**You:** "The Nextcloud token expired, update it to user:yyyyy-yyyyy"

**AI Agent:** *Calls `mcp_home_update_service` with name "nextcloud", api_token "user:yyyyy-yyyyy"*

"Updated. The Nextcloud connection is using the new credentials and tested successfully."

**You:** "Disable the nextcloud_user_status tool, I don't need it"

**AI Agent:** *Calls `mcp_home_toggle_tool` to disable nextcloud_user_status*

"Done. nextcloud_user_status is now disabled and won't appear in future sessions."

### Access Control

- **Admin users** — Full access to all self-management tools
- **Non-admin users** — When `self_mcp_enabled` is toggled on for their account, they get read-only self-MCP tools scoped to their assigned services. They cannot add services, manage tools, or view other users' audit logs.
- Admins control the `self_mcp_enabled` flag per user from the [user management](users-api-keys) page.

### Disabling Self-MCP

To remove all self-management tools from the MCP endpoint globally, either turn off the toggle in **Settings > Security**, or set in your `.env` file:

```bash
SELF_MCP_ENABLED=false
```

Then restart MCP Home Manager:

```bash
docker compose restart app
```

When disabled, no self-management tools or UI apps are exposed to any user. Service tools continue to work normally.

### Related

- [Users & API Keys](users-api-keys) — Per-user self-MCP toggle
- [Audit Logs](audit-logs) — Querying logs via self-MCP
- [Generic REST](generic-rest) — Managing custom tools via self-MCP
