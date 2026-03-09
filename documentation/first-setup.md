## First Setup

After [installing](installation) MCP Home Manager, complete the one-time setup to create your admin account and connect your first service.

### Create Your Admin Account

:::steps
1. **Open the web UI** — Navigate to `http://your-server:8000`. You will be automatically redirected to the setup page.

2. **Fill in your details**:
   - **Username** — Minimum 2 characters
   - **Email** — Optional, used for password reset emails
   - **Password** — Minimum 8 characters, enter it twice to confirm

3. **Save your API key** — After creating your account, the setup page displays your API key. **Copy it now** — the key is shown only once. It is hashed after this screen and cannot be recovered. If you lose it, you can generate a new one from your account settings.
:::

:::info API Key Security
Your API key is how AI agents authenticate with MCP Home Manager. Treat it like a password — do not share it or commit it to version control. If compromised, revoke it immediately from the web UI and generate a new one.
:::

### Explore the Dashboard

After setup, you land on the dashboard. From here you can:

- View connected service health at a glance
- See recent activity
- Navigate to service management

### Add Your First Service

:::steps
1. **Go to Services** — Click "Services" in the sidebar
2. **Add a service** — Click "Add Service"
3. **Choose the service type** — Select from the 17 built-in adapters or use Generic REST
4. **Enter connection details** — Provide the service URL and credentials (format varies by service — see the [Connecting Services](connecting-services) guide)
5. **Test the connection** — The connection is tested automatically on save
:::

### Configure Your AI Agent

Point your AI agent at the MCP endpoint using your API key:

- **Endpoint URL:** `http://your-server:8000/mcp/`
- **Authentication:** `Authorization: Bearer YOUR_API_KEY`

For detailed setup instructions for each AI agent:

- [Claude Desktop](claude-desktop)
- [Claude Code](claude-code)
- [Cursor](cursor)
- [ChatGPT](chatgpt)
- [Codex](codex)

### What's Next

- [Connecting Services](connecting-services) — Detailed guide for connecting each service type
- [Environment Variables](environment-variables) — Fine-tune your configuration
- [Multi-User](multi-user) — Add more users with scoped access
- [Self-MCP](self-mcp) — Manage MCP Home Manager through your AI agent
