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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the key from [First Setup](first-setup).

### Verify

Run `/mcp show` inside a Copilot CLI session to see connected servers and their status.

### When Services Change

Copilot CLI caches the tool list at startup. When you connect or remove services in MCP Home Manager, restart Copilot CLI to pick up the new tools.
