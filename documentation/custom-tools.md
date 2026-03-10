## Custom Tools

You can add custom tool definitions to any service — not just Generic REST. This covers two use cases:

- **Extending a built-in service** with API endpoints its adapter doesn't cover. For example, adding a custom Home Assistant tool that calls a specific automation endpoint.
- **Defining tools for a fully custom API** via [Generic REST](generic-rest), where every tool is manually defined.

### Adding a Custom Tool

On any service detail page, click **Add Tool** to define a new tool, or **Import OpenAPI** to import tools from an OpenAPI 3.x spec.

### Tool Definition Format

```json
{
  "name": "get_temperature",
  "description": "Get current temperature reading from a specific sensor",
  "method": "GET",
  "path": "/api/sensors/{sensor_id}/temperature",
  "parameters": {
    "sensor_id": {
      "type": "string",
      "description": "The sensor ID to query",
      "required": true
    }
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Tool name. Gets prefixed with the service name (e.g., `myservice_get_temperature`). |
| `description` | Yes | What the tool does. Agents use this to decide when to call the tool — be specific. |
| `method` | Yes | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`. |
| `path` | Yes | URL path appended to the service base URL. Use `{param_name}` for path parameters. |
| `parameters` | No | JSON Schema object describing the tool's input parameters. Each parameter needs a `type`, `description`, and optionally `required: true`. |

The `description` field matters — AI agents read it to decide when to invoke the tool. Write a clear, specific description of what the tool returns and when to use it.

### Related

- [Generic REST](generic-rest) — Service type for fully custom APIs
- [OpenAPI Import](openapi-import) — Bulk-import tools from an OpenAPI spec
- [Self-MCP](self-mcp) — Manage custom tools via AI agent (`mcp_home_add_generic_tool`, `mcp_home_update_generic_tool`, `mcp_home_delete_generic_tool`)
