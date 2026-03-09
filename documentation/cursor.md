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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the API key from [First Setup](first-setup).
