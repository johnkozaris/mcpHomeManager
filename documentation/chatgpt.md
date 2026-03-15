## ChatGPT

ChatGPT supports remote MCP servers through Developer Mode. Unlike Claude Code or Cursor, ChatGPT connects to your server over the internet — it does not read a local config file.

### Prerequisites

- ChatGPT Plus or Pro subscription
- A publicly accessible MCP endpoint (HTTPS required — ChatGPT connects over the public internet, so TLS is required for security)

:::info Public Endpoint Required
ChatGPT connects to your MCP server from OpenAI's infrastructure, not from your local machine. Your endpoint must be reachable over the internet via HTTPS. Use a [reverse proxy](reverse-proxy) with a domain and TLS certificate, or a tunnel service like Cloudflare Tunnel. Exposing your MCP endpoint to the internet is your responsibility — review the [security](security) guide and understand the risks before proceeding.
:::

:::info What Is a Reverse Proxy?
A reverse proxy sits in front of your server and handles HTTPS. See [Reverse Proxy](reverse-proxy) for setup guides with Nginx, Caddy, or Traefik.
:::

### Setup

:::steps
1. **Enable Developer Mode** — Go to **Settings > Apps & Connectors > Advanced settings** and enable Developer Mode

2. **Create a connector** — Back in Apps & Connectors, click **Create** and select **MCP Server**

3. **Enter your endpoint** — Provide a name (e.g., "My Homelab") and paste your public endpoint URL:

```
https://mcp.your-domain.com/mcp/
```

4. **Click Create** — New conversations will automatically discover your homelab tools
:::

Use the public hostname from your [reverse proxy](reverse-proxy) setup.

### Authentication

Pass your API key as a query parameter in the endpoint URL:

```
https://mcp.your-domain.com/mcp/?api_key=YOUR_API_KEY
```

Alternatively, if ChatGPT's connector supports custom headers in your account, set an `Authorization: Bearer YOUR_API_KEY` header. Check [OpenAI's MCP documentation](https://developers.openai.com/api/docs/mcp/) for the latest on authentication options — the connector is still evolving.

### Verify

Create a new conversation and check that your homelab tools appear. Try asking ChatGPT to interact with a connected service.

### When Services Change

MCP Home Manager registers new tools immediately. ChatGPT caches tools at the start of a conversation — start a new conversation to see changes.

### MCP Apps

ChatGPT has begun rolling out support for MCP Apps (interactive HTML content returned by tools). Services like Home Assistant's entity dashboard may render as interactive panels in your conversation.

### Limitations

- Only available with ChatGPT Plus or Pro
- Requires a publicly accessible HTTPS endpoint (no local-only setups)
- Developer Mode is still in beta — behavior may change
