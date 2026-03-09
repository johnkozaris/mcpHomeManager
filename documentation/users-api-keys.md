## Users & API Keys

MCP Home Manager uses API keys to authenticate AI agents. Each user has their own API key with scoped access to their assigned services.

### API Key Lifecycle

**Generate** — A new API key is created during [first setup](first-setup) for the admin account. Additional users can generate their own keys from their account settings, or admins can manage keys from the user management page.

**Reveal** — After generation, the plaintext API key can be viewed once. After the initial reveal, only the SHA-256 hash is stored. If you navigate away without copying the key, you will need to generate a new one.

**Revoke** — Revoking a key immediately invalidates it. Any AI agent using that key will lose access. A new key can be generated afterward.

:::info API Key Security
- API keys are hashed (SHA-256) before storage — MCP Home Manager cannot recover a lost key
- Each user can have one active API key at a time
- Generating a new key replaces the previous one
- Treat API keys like passwords — do not share or commit them to version control
:::

### Creating Users

Admin users can create new accounts:

:::steps
1. **Go to Users** — Click "Users" in the sidebar
2. **Click "Add User"**
3. **Fill in details** — Username (min 2 chars), optional email, password (min 8 chars)
4. **Set role** — Toggle admin role on or off
5. **Assign services** — Select which services this user can access
6. **Save**
:::

### Per-User Service Access

Non-admin users only see and interact with their assigned services:

- Their MCP endpoint only exposes tools from assigned services
- Their audit logs only show their own activity
- Admins can update service assignments at any time

### Self-MCP Toggle

Each user has a `self_mcp_enabled` flag that controls whether [self-management tools](self-mcp) are exposed in their MCP endpoint. Admins can toggle this per user.

When enabled for non-admin users, only read-only self-MCP tools for their assigned services are available.

### Password Reset

**Via web UI** — From the login page, click "Forgot password" (requires SMTP configuration).

**Via email** — A time-limited reset link (1-hour expiry) is sent to the user's email address. Always returns a success response regardless of whether the email exists (prevents user enumeration).

**Via CLI** — Admins can reset passwords directly:

```bash
docker compose exec app uv run mcp-home-reset-password
```

### Related

- [Multi-User](multi-user) — Role-based access control and service isolation
- [Self-MCP](self-mcp) — Managing MCP Home Manager through your AI agent
