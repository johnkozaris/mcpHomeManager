## GitHub Copilot CLI

Add MCP Home Manager to GitHub Copilot CLI using the interactive command or by editing the config file.

### Option 1: Interactive

Inside a Copilot CLI session, run:

```
/mcp add homelab
```

Select **HTTP** as the transport type, enter your endpoint URL and API key when prompted.

### Option 2: Config File

Create or edit `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "homelab": {
      "type": "http",
      "url": "http://your-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

For project-scoped configuration, place `.copilot/mcp-config.json` in your project root instead.

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from [First Setup](first-setup).

### Verify

Run `/mcp show` inside a Copilot CLI session to see connected servers and their status.

### When Services Change

MCP Home Manager registers new tools immediately. Copilot CLI caches tools at startup — restart it to see changes.
