## Claude Code

Add MCP Home Manager to Claude Code using the CLI or a project config file.

### Getting Your API Key

Go to **Settings > MCP API Key** in the web UI. Click **Reveal Key** to see your existing key, or **Generate Key** if you haven't created one yet. Copy the key — you'll need it for the commands below.

### Option 1: CLI

```bash
claude mcp add homelab \
  --transport http \
  --header "Authorization: Bearer YOUR_API_KEY" \
  http://your-server:8000/mcp/
```

### Option 2: Project Config File

Create a `.mcp.json` file at the root of your project:

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

Add `.mcp.json` to your `.gitignore` — it contains your API key.

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from the step above.

### Verify

After adding the server, your homelab tools will be available in Claude Code. Run `claude mcp list` to confirm the server is connected, then try asking Claude to interact with a connected service.

### When Services Change

MCP Home Manager registers new tools immediately. Claude Code caches tools at startup — restart it to see changes.
