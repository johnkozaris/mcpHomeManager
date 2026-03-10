## ChatGPT

ChatGPT supports remote MCP servers through Developer Mode. Unlike Claude Code or Cursor, ChatGPT connects to your server over the internet — it does not read a local config file.

### Prerequisites

- ChatGPT Plus or Pro subscription
- A publicly accessible MCP endpoint (HTTPS required)

:::info Public Endpoint Required
ChatGPT connects to your MCP server from OpenAI's infrastructure, not from your local machine. Your endpoint must be reachable over the internet via HTTPS. Use a [reverse proxy](reverse-proxy) with a domain and TLS certificate, or a tunnel service like Cloudflare Tunnel. Exposing your MCP endpoint to the internet is your responsibility — review the [security](security) guide and understand the risks before proceeding.
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

Replace `mcp.your-domain.com` with the public hostname of your MCP Home Manager instance.

### Authentication

ChatGPT's MCP connector currently uses its own authentication flow. Pass your API key in the endpoint configuration. Check [OpenAI's MCP documentation](https://developers.openai.com/api/docs/mcp/) for the latest on authentication options.

### MCP Apps

ChatGPT has begun rolling out support for MCP Apps (interactive HTML content returned by tools). Services like Home Assistant's entity dashboard may render as interactive panels in your conversation.

### Limitations

- Only available with ChatGPT Plus or Pro
- Requires a publicly accessible HTTPS endpoint (no local-only setups)
- Developer Mode is still in beta — behavior may change
