## Claude Code

Add MCP Home Manager to Claude Code using the CLI or settings file.

### Option 1: CLI

```bash
claude mcp add homelab \
  --transport streamable-http \
  --url http://your-server:8000/mcp/ \
  --header "Authorization: Bearer YOUR_API_KEY"
```

### Option 2: Settings File

Add to your `.claude/settings.json`:

```json
{
  "mcpServers": {
    "homelab": {
      "type": "streamable-http",
      "url": "http://your-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the API key from [First Setup](first-setup).

### Verify

After adding the server, your homelab tools will be available in Claude Code. You can verify by asking Claude to list available tools or interact with a connected service.
