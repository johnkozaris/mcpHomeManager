## AdGuard Home

Monitor and manage your DNS filtering through your AI agent. Check filtering status, view query logs, and review DNS statistics.

### What You Can Do

- Check DNS filtering status and protection state
- View DNS query logs
- Get filtering statistics
- List DNS filter lists and rewrite rules
- Toggle DNS protection on or off

### Prerequisites

- AdGuard Home instance accessible from MCP Home Manager
- Your AdGuard Home admin username and password

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** AdGuard Home
- **URL:** Your AdGuard Home URL (e.g., `http://192.168.1.100:3000`)
- **Credentials:** `username:password` format (e.g., `admin:your-password`)

### Available Tools

:::tools
- `adguard_status` — Get current AdGuard Home status (protection enabled/disabled, version, etc.)
- `adguard_query_log` — View recent DNS query log entries
- `adguard_stats` — Get filtering statistics (queries, blocked, etc.)
- `adguard_list_filters` — List all configured DNS filter lists
- `adguard_list_rewrites` — List DNS rewrite rules
- `adguard_toggle_protection` — Enable or disable DNS protection
:::

### Limitations

- **Stats lookback** — Statistics lookback period must be specified in whole hours
- **Read-only filters** — Cannot add, remove, or modify DNS filter lists or rewrite rules (only listing is supported)

### Example Prompts

- "Is AdGuard protection currently enabled?"
- "Show me the last 50 DNS queries"
- "How many queries were blocked today?"
- "What filter lists are configured?"
- "Disable DNS protection temporarily"
