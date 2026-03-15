## Cursor

Add MCP Home Manager to Cursor's MCP configuration.

### Configuration

:::steps
1. **Open Cursor settings** — Settings → MCP
2. **Add a new server** with the following configuration:

```json
{
  "name": "homelab",
  "url": "http://your-server:8000/mcp/",
  "headers": {
    "Authorization": "Bearer YOUR_API_KEY"
  }
}
```

3. **Save** — Your homelab tools will be available in Cursor's AI assistant.
:::

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from [First Setup](first-setup).

:::info Finding MCP Settings
Open Cursor, then go to **Settings** (gear icon or `Cmd/Ctrl+,`) → search for **MCP** in the sidebar. The MCP server list is under **Features → MCP**.
:::

### Verify

After saving, open a new Cursor AI chat and check that your homelab tools appear. Try asking the assistant to interact with a connected service.

### When Services Change

MCP Home Manager registers new tools immediately. Cursor caches tools at startup — restart it to see changes.
