## Connecting Services

MCP Home Manager connects to your homelab services using their APIs. Each service needs a URL and credentials. Once connected, your AI agent can interact with the service through MCP tools.

### How Connections Work

When you connect a service, MCP Home Manager:
1. Encrypts and stores the credentials in PostgreSQL
2. Tests the connection immediately
3. Registers the service's tools with the MCP endpoint
4. Begins periodic health checks

### Adding a Service

:::steps
1. **Navigate to Services** — Click "Services" in the sidebar
2. **Click "Connect Service"**
3. **Select the service type** — Choose from the 17 built-in adapters or Generic REST
4. **Enter the base URL** — The URL where the service API is reachable (e.g., `http://192.168.1.100:8123`)
5. **Enter credentials** — Format depends on the service type (see table below)
6. **Save** — The connection is tested automatically. If it fails, check the URL and credentials.
:::

### After Connecting

Tools are registered on the MCP endpoint immediately. Most MCP clients discover them right away. Claude Code, Cursor, and Copilot cache the tool list at startup — restart them to see newly added tools.

### Service Name and Display Name

Each service has a **name** (slug) and a **display name**. The name is used as a prefix for all the service's tools — for example, a Forgejo service named `forgejo` produces tools like `forgejo_list_repos`, `forgejo_create_issue`, etc. The display name appears in the web UI and has no effect on tool names.

Choose a short, descriptive name. If you connect multiple services of the same type, give them distinct names (e.g., `forgejo_work`, `forgejo_personal`).

### Credential Formats

Each service type expects credentials in a specific format:

| Service | Credential Format | Example |
|---------|-------------------|---------|
| [Home Assistant](home-assistant) | Long-lived access token | `eyJhbG...` |
| [Paperless-ngx](paperless-ngx) | API token | `abc123def456...` |
| [Immich](immich) | API key | `abc123def456...` |
| [Forgejo](forgejo) | Personal access token | `abc123def456...` |
| [Uptime Kuma](uptime-kuma) | `username:password` (optional 2FA: `user:pass:123456`) | `admin:your-password` |
| [Nextcloud](nextcloud) | `username:app-password` | `user:xxxxx-xxxxx-xxxxx` |
| [AdGuard Home](adguard) | `username:password` | `admin:your-password` |
| [Portainer](portainer) | API key, or `username:password` | `ptr_abc...` or `admin:pass` |
| [Nginx Proxy Manager](nginx-proxy-manager) | `email:password` | `admin@example.com:your-password` |
| [FreshRSS](freshrss) | `username:password` | `admin:your-password` |
| [Wallabag](wallabag) | `client_id:client_secret:username:password` | `1_abc:xyz:user:pass` |
| [Calibre-Web](calibre-web) | `username:password` | `admin:your-password` |
| [Wiki.js](wikijs) | API key (Bearer token) | `eyJhbG...` |
| [Tailscale](tailscale) | API key | `tskey-api-...` |
| [Cloudflare](cloudflare) | API token (Bearer) | `abc123def456...` |
| [Stirling PDF](stirling-pdf) | API key | `your-api-key` |
| [Generic REST](generic-rest) | Varies (Bearer, API key, Basic, or none) | Depends on target API |

For services not in this list, use [Generic REST](generic-rest) to define custom API endpoints.

### Managing Tools

After connecting a service, you can enable or disable individual tools:

1. Go to **Services** → click on the service
2. View the list of available tools
3. Toggle tools on or off as needed

Disabled tools are not exposed to your AI agent via the MCP endpoint.

### Health Monitoring

MCP Home Manager periodically checks the health of connected services (default: every 60 seconds, configurable via `HEALTH_CHECK_INTERVAL_SECONDS`).

Health status is shown in the web UI dashboard and available via the [self-management tools](self-mcp).

| Status | Meaning |
|--------|---------|
| Healthy | Service responded successfully |
| Unhealthy | Service did not respond or returned an error |
| Unknown | Not yet checked |

### Editing and Removing Services

- **Edit** — Click on a service to update its URL, credentials, or display name
- **Remove** — Delete a service from the service detail page. This removes the connection and all associated tool permissions. Audit logs for the service are preserved.
