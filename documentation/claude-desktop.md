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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the API key from [First Setup](first-setup).

If you're using a reverse proxy with HTTPS, use your public URL instead (e.g., `https://mcp.your-domain.com/mcp/`).

### MCP Apps

Claude Desktop supports interactive HTML apps served by MCP Home Manager. Services that provide MCP apps (like Home Assistant's entity dashboard) will appear as interactive UI panels in your conversation.
