## Users & Access Control

MCP Home Manager supports multiple users with role-based access. Each user gets their own API key and can only access their assigned services.

### Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access to all services, manage users, manage settings, view all audit logs |
| **User** | Access only assigned services, manage own API key, view own audit logs |

The first account created during [initial setup](first-setup) is always an admin.

### Adding Users

:::steps
1. **Go to Users** — Click "Users" in the sidebar (admin only)
2. **Click "Add User"**
3. **Fill in details** — Username (min 2 chars), optional email, password (min 8 chars)
4. **Set role** — Toggle admin on or off
5. **Assign services** — Select which services this user can access
6. **Save**
:::

### Service Isolation

Each non-admin user sees only their assigned services:

- Only tools from assigned services appear in their MCP endpoint
- Audit logs record which user made each tool call
- Admins can update service assignments at any time

### API Keys

Each user has their own API key for connecting AI agents.

- **Generate** — Created during [first setup](first-setup) for the admin. Other users generate keys from account settings, or admins can trigger it from user management.
- **Reveal** — The plaintext key is shown once after generation. After that, only the hash is stored. Copy it before navigating away.
- **Revoke** — Immediately invalidates the key. A new one can be generated afterward.

:::info API Key Security
API keys are hashed (SHA-256) before storage. MCP Home Manager cannot recover a lost key. Each user has one active key at a time. Generating a new key replaces the old one. Treat keys like passwords.
:::

### Self-MCP Per User

Admins can enable or disable [self-management tools](self-mcp) per user via the `self_mcp_enabled` flag. When enabled for non-admin users, only read-only self-MCP tools scoped to their assigned services are available.

### Password Reset

- **Web UI** — From the login page, click "Forgot password" (requires SMTP configured)
- **Email** — A time-limited reset link (1-hour expiry) is sent to the user's email
- **CLI** — Admins can reset passwords directly:

```bash
docker compose exec app uv run mcp-home-reset-password
```

The CLI command prompts for a username and new password interactively.
