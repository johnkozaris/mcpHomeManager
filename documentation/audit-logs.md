## Audit Logs

MCP Home Manager logs every AI tool call, providing a complete record of what your AI agents did, when, and on which service.

### What's Logged

Each tool call records:

| Field | Description |
|-------|-------------|
| Timestamp | When the tool was called |
| User | Which user (API key) made the call |
| Tool name | The MCP tool that was invoked |
| Service | Which connected service was targeted |
| Parameters | The arguments passed to the tool |
| Status | Whether the call succeeded or failed |
| Duration | How long the call took (milliseconds) |

### Viewing Audit Logs

**From the web UI:**

Navigate to the audit logs section in the sidebar. You can filter by:
- User
- Service
- Time range
- Status (success/failure)

**Via self-MCP:**

If [self-management tools](self-mcp) are enabled, your AI agent can query audit logs directly:

```
"Show me all tool calls from the last hour"
"What did user admin do on the Home Assistant service today?"
"Were there any failed tool calls this week?"
```

The `mcp_home_get_logs` self-MCP tool supports filtering by user, service, and time range.

### Per-User Logs

- **Admin users** can view audit logs for all users
- **Non-admin users** can only view their own activity

### Retention

Audit logs are stored in the database (SQLite by default, or PostgreSQL if configured). There is no automatic retention policy — logs grow over time. For large installations, consider periodically archiving or cleaning old records directly in the database.
