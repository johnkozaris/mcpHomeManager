## OpenCode

Add MCP Home Manager to OpenCode by editing the config file.

### Prerequisites

- OpenCode installed
- Your MCP Home Manager API key from [First Setup](first-setup)

### Configuration

Add a remote MCP server entry to `opencode.json` — either globally at `~/.config/opencode/opencode.json` or in your project root:

```json
{
  "mcp": {
    "homelab": {
      "type": "remote",
      "url": "http://your-server:8000/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from [First Setup](first-setup).

### Verify

Your homelab tools will be available to the LLM alongside built-in tools once OpenCode connects to the server.

### When Services Change

MCP Home Manager registers new tools immediately. OpenCode caches tools at startup — restart it to see changes.
