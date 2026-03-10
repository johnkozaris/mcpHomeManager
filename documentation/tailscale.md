## Tailscale

Manage your Tailscale network through your AI agent. View devices, manage authorization, and check DNS configuration.

### What You Can Do

- List devices on your tailnet
- View device details and routes
- Authorize new devices
- Check DNS nameserver configuration

### Prerequisites

- A Tailscale account with admin access
- A Tailscale API key

### Getting Your API Key

:::steps
1. **Open the Tailscale admin console** — Navigate to [admin.tailscale.com](https://admin.tailscale.com)
2. **Go to Settings** — Settings → Keys
3. **Generate an API key** — Create a new API key (starts with `tskey-api-`)
4. **Copy the key** — Save it securely
:::

:::info API Key Permissions
Ensure your API key has the appropriate ACL permissions for the operations you want to perform. Read-only keys can list devices; write keys are needed for authorization.
:::

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Tailscale
- **URL:** `https://api.tailscale.com` (this is the default — Tailscale uses a cloud API)
- **Credentials:** Paste your API key (e.g., `tskey-api-abc123...`)

### Available Tools

:::tools
- `tailscale_list_devices` — List all devices on your tailnet
- `tailscale_get_device` — Get detailed information about a specific device
- `tailscale_authorize_device` — Authorize a pending device
- `tailscale_get_device_routes` — Get subnet routes for a device
- `tailscale_list_dns_nameservers` — List configured DNS nameservers
:::

### Limitations

- **Cloud API** — Operates against the Tailscale cloud API (`api.tailscale.com`), not a local service. Requires internet access from your MCP Home Manager instance.
- **ACL permissions** — The API key must have appropriate ACL permissions for the operations you want to perform
- **No device removal** — Cannot remove devices from the tailnet through MCP

### Example Prompts

- "List all devices on my tailnet"
- "Is the home-server device online?"
- "Authorize the new device waiting for approval"
- "What routes are configured on the gateway device?"
- "What DNS nameservers are configured?"
