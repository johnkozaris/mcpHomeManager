## Cloudflare

Manage your Cloudflare DNS records and tunnels through your AI agent.

### What You Can Do

- List DNS zones
- View, create, and manage DNS records
- List and view Cloudflare Tunnels

### Prerequisites

- A Cloudflare account
- A scoped API token (not the global API key)

### Getting Your API Token

:::steps
1. **Open the Cloudflare dashboard** — Navigate to [dash.cloudflare.com](https://dash.cloudflare.com)
2. **Go to API Tokens** — Click your avatar → My Profile → API Tokens
3. **Create a token** — Click "Create Token"
4. **Set permissions** — Choose the zones and permissions you need:
   - DNS read/write for managing DNS records
   - Zone read for listing zones
   - Cloudflare Tunnel read for listing tunnels
5. **Copy the token** — Save it securely
:::

:::info Use Scoped Tokens
Always use a scoped API token with the minimum permissions needed. Do **not** use the Global API Key, as it grants full account access.
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** Cloudflare
- **URL:** `https://api.cloudflare.com/client/v4` (this is the default Cloudflare API endpoint)
- **Credentials:** Paste your API token

### Available Tools

:::tools
- `cloudflare_list_zones` — List all DNS zones in your account
- `cloudflare_list_dns_records` — List DNS records for a specific zone
- `cloudflare_create_dns_record` — Create a new DNS record in a zone
- `cloudflare_list_tunnels` — List Cloudflare Tunnels
- `cloudflare_get_tunnel` — Get detailed information about a specific tunnel
:::

### Limitations

- **Scoped permissions** — The API token must have permissions for the specific zones and tunnels you want to manage. Operations on resources outside the token's scope will fail.
- **No DNS deletion** — Cannot delete DNS records through MCP
- **Cloud API** — Operates against the Cloudflare cloud API. Requires internet access from your MCP Home Manager instance.

### Example Prompts

- "List all my Cloudflare zones"
- "Show the DNS records for example.com"
- "Create an A record for app.example.com pointing to 203.0.113.50"
- "List my Cloudflare tunnels"
- "Show me the details of the homelab tunnel"
