## Multi-User & Access Control

MCP Home Manager supports multiple users with role-based access control. Each user gets their own API key and can only access the services assigned to them.

### Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access to all services, manage users, manage settings, view all audit logs |
| **User** | Access only to assigned services, manage own API key, view own audit logs |

The first account created during [initial setup](first-setup) is always an admin.

### Adding Users

:::steps
1. **Go to Users** — Click "Users" in the sidebar (admin only)
2. **Click "Add User"**
3. **Fill in details:**
   - **Username** — Minimum 2 characters, must be unique
   - **Email** — Optional, used for password reset emails
   - **Password** — Minimum 8 characters
   - **Admin** — Toggle admin role on or off
4. **Assign services** — Select which services this user can access
5. **Save**
:::

### Service Isolation

Each non-admin user sees only their assigned services. When they connect with their API key:

- Only tools from assigned services appear in the MCP endpoint
- Audit logs record which user made each tool call
- Admin users can adjust service assignments at any time

### Per-User API Keys

Each user has their own API key for connecting AI agents:

- **Generate** — Users can generate an API key from their account settings, or admins can trigger it from the user management page
- **Reveal** — The API key can be viewed once after generation. After that, only the hash is stored.
- **Revoke** — Revoking a key immediately invalidates it. A new key can be generated afterward.

### Self-MCP Access

Admins can enable or disable [self-management tools](self-mcp) per user via the `self_mcp_enabled` flag. When enabled, the user's MCP endpoint includes self-management tools (scoped to their access level).

### Password Reset

Users can reset their password through several methods:

- **Web UI** — From the login page, click "Forgot password" (requires SMTP configuration)
- **Email** — A time-limited reset link is sent to the user's email address (1-hour expiry)
- **CLI** — Admins can reset a user's password from the command line:

```bash
docker compose exec app uv run mcp-home-reset-password
```

### Related

- [Users & API Keys](users-api-keys) — Detailed API key lifecycle management
- [Audit Logs](audit-logs) — View per-user activity logs
