## OpenCode

Add MCP Home Manager to OpenCode by editing the config file.

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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the key from [First Setup](first-setup).

### Verify

Your homelab tools will be available to the LLM alongside built-in tools once OpenCode connects to the server.

### When Services Change

Restart OpenCode to pick up newly added or removed tools.
