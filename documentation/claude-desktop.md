## Claude Desktop

Add MCP Home Manager to your Claude Desktop configuration file.

### Configuration

:::steps
1. **Open Claude Desktop settings** — Click the menu icon → Settings → Developer → Edit Config
2. **Add the MCP server** — Paste the following into your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "homelab": {
      "url": "http://your-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

3. **Restart Claude Desktop** — Your homelab tools will appear in the tool list.
:::

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from [First Setup](first-setup). If you're using a reverse proxy with HTTPS, use your public URL instead (e.g., `https://mcp.your-domain.com/mcp/`).

:::info Developer Settings
The MCP server configuration requires Claude Desktop's Developer settings to be enabled. Open Settings → Developer to access the config editor.
:::

### Verify

Open Claude Desktop and look for your homelab tools in the tool picker. Try asking Claude to interact with a connected service (e.g., "list my Home Assistant entities").

### When Services Change

MCP Home Manager registers new tools immediately. Claude Desktop caches tools at startup — restart it to see changes.

### MCP Apps

Claude Desktop supports interactive HTML apps served by MCP Home Manager. Services that provide MCP apps (like Home Assistant's entity dashboard) will appear as interactive UI panels in your conversation.
