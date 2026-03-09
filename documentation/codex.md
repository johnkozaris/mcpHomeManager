## Codex (OpenAI)

Add MCP Home Manager to your Codex MCP configuration.

### Configuration

Add the following to your Codex MCP server configuration:

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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the API key from [First Setup](first-setup).
