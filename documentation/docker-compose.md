## Docker Compose

MCP Home Manager runs as a single Docker container with an embedded SQLite database. The compose file works without any `.env` file — just paste it and deploy.

### Default Configuration

The `docker-compose.yml` included in the repository:

```yaml
services:
  app:
    image: ghcr.io/johnkozaris/mcp-home-manager:latest
    restart: unless-stopped
    ports:
      - "${APP_PORT:-8000}:8000"
    environment:
      APP_NAME: ${APP_NAME:-MCP Manager}
      PUBLIC_URL: ${PUBLIC_URL:-http://localhost:8000}
      MCP_SERVER_NAME: ${MCP_SERVER_NAME:-My Homelab}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:-}
    volumes:
      - app_data:/app/data    # encryption key + SQLite database
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true

volumes:
  app_data:
```

Every variable has a `:-default` fallback, so the compose file is self-contained. No `.env` file is needed — just `docker compose up -d`.

### Service

**`app` — MCP Home Manager**

The application server serves both the web UI and the MCP endpoint. The SQLite database is stored in the `app_data` volume alongside the encryption key.

Key security features:
- `read_only: true` — Container filesystem is read-only. Only `/tmp` (tmpfs) and `/app/data` (volume) are writable.
- `cap_drop: [ALL]` — All Linux capabilities removed.
- `no-new-privileges` — Prevents privilege escalation.
- The container runs as a non-root user (`appuser`).

### Volume

| Volume | Mount | Purpose |
|--------|-------|---------|
| `app_data` | `/app/data` | SQLite database and auto-generated encryption key |

:::info Back Up Your Volume
The `app_data` volume contains your database and encryption key. Without the encryption key, stored service credentials cannot be decrypted.
:::

### Customization

To override any default, create a `.env` file alongside `docker-compose.yml`:

**Change the host port:**

```bash
APP_PORT=9000
```

**Pin a specific version:**

Instead of `:latest`, edit the `image:` line in `docker-compose.yml` directly, or use the version-pinned compose file from a [GitHub Release](https://github.com/johnkozaris/mcpHomeManager/releases).

See the full list of configuration options in [Environment Variables](environment-variables).

### Using PostgreSQL

For larger deployments or if you prefer an external database, use the PostgreSQL override file:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d
```

This adds a PostgreSQL container and configures the app to use it instead of SQLite. See [Environment Variables](environment-variables) for the `POSTGRES_*` and `DATABASE_URL` options.

Alternatively, point at any existing PostgreSQL instance by setting `DATABASE_URL` in your `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@external-db:5432/mcp_home
```
