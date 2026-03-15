## Uptime Kuma

Monitor your services and manage uptime monitors through your AI agent.

### What You Can Do

- View all monitors and their current status
- Get detailed information about specific monitors
- Pause and resume monitors

### Prerequisites

- Uptime Kuma instance accessible from MCP Home Manager
- Your Uptime Kuma username and password

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Uptime Kuma
- **URL:** Your Uptime Kuma URL (e.g., `http://192.168.1.100:3001`)
- **Credentials:** `username:password` format (e.g., `admin:your-password`)

If you have two-factor authentication enabled, append the TOTP code:
- **Credentials with 2FA:** `username:password:123456`

### Available Tools

:::tools
- `uptimekuma_list_monitors` — List all monitors with their current status
- `uptimekuma_get_monitor` — Get detailed information about a specific monitor
- `uptimekuma_pause_monitor` — Pause a running monitor
- `uptimekuma_resume_monitor` — Resume a paused monitor
:::

### Limitations

- **WebSocket connection** — Uptime Kuma uses WebSocket connections (via Socket.IO) instead of a REST API. The initial connection may be slower to establish compared to REST-based services.
- **No heartbeat history** — Cannot retrieve historical heartbeat data
- **2FA requires current code** — If 2FA is enabled, you must update the credentials with a fresh TOTP code each time the connection needs to re-authenticate. Consider creating a dedicated account without 2FA for MCP Home Manager.

### Example Prompts

- "What's the status of all my monitors?"
- "Is my website currently up?"
- "Pause the staging-server monitor"
- "Resume all paused monitors"
- "Show me the details of the database monitor"
