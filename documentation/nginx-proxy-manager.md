## Nginx Proxy Manager

Manage your reverse proxy hosts through your AI agent. View, create, and manage proxy host configurations.

### What You Can Do

- List and view proxy host configurations
- Create new proxy hosts
- Delete proxy hosts
- List redirection hosts, streams, and SSL certificates

### Prerequisites

- Nginx Proxy Manager instance accessible from MCP Home Manager
- Your NPM admin email and password

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Nginx Proxy Manager
- **URL:** Your NPM URL (e.g., `http://192.168.1.100:81`)
- **Credentials:** `email:password` format (e.g., `admin@example.com:your-password`)

### Available Tools

:::tools
- `npm_list_proxy_hosts` — List all proxy host configurations
- `npm_get_proxy_host` — Get detailed configuration for a specific proxy host
- `npm_create_proxy_host` — Create a new proxy host
- `npm_delete_proxy_host` — Delete a proxy host
- `npm_list_redirection_hosts` — List redirection host configurations
- `npm_list_streams` — List TCP/UDP stream configurations
- `npm_list_certificates` — List SSL certificates
:::

### Limitations

- **No 2FA support** — Accounts with two-factor authentication enabled are not currently supported
- **Email/password auth only** — Authentication uses NPM's JWT login with email and password

### Example Prompts

- "List all my proxy hosts"
- "Show me the config for the Home Assistant proxy"
- "Create a proxy host for app.example.com pointing to 192.168.1.50:3000"
- "What SSL certificates do I have?"
- "List my redirection hosts"
