## Docker Compose

MCP Home Manager uses a two-service Docker Compose stack: the application server and a PostgreSQL database. The compose file works without any `.env` file — just paste it and deploy.

### Default Configuration

The `docker-compose.yml` included in the repository:

```yaml
services:
  db:
    image: ${POSTGRES_IMAGE:-postgres:17-alpine}
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-mcp_home}
      POSTGRES_USER: ${POSTGRES_USER:-mcp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mcp}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$$POSTGRES_USER\" -d \"$$POSTGRES_DB\""]
      interval: 5s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true

  app:
    image: ghcr.io/johnkozaris/mcp-home-manager:latest
    restart: unless-stopped
    ports:
      - "${APP_PORT:-8000}:8000"
    environment:
      POSTGRES_HOST: ${POSTGRES_HOST:-db}
      POSTGRES_PORT: ${POSTGRES_PORT:-5432}
      POSTGRES_DB: ${POSTGRES_DB:-mcp_home}
      POSTGRES_USER: ${POSTGRES_USER:-mcp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mcp}
      APP_NAME: ${APP_NAME:-MCP Manager}
      PUBLIC_URL: ${PUBLIC_URL:-http://localhost:8000}
      MCP_SERVER_NAME: ${MCP_SERVER_NAME:-My Homelab}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:-}
    volumes:
      - app_data:/app/data
    depends_on:
      db:
        condition: service_healthy
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true

volumes:
  pgdata:
  app_data:
```

Every variable has a `:-default` fallback, so the compose file is self-contained. No `.env` file is needed — just `docker compose up -d`.

### Services

**`db` — PostgreSQL database**

Stores all persistent data: service connections, user accounts, tool permissions, and audit logs. Credentials are encrypted at the application level before being written to the database.

The default database password (`mcp`) is safe because the database runs on an isolated Docker network and is not exposed to the host. Override it via `.env` if your environment requires it.

The healthcheck ensures the application container does not start until the database is ready to accept connections.

**`app` — MCP Home Manager**

The application server serves both the web UI and the MCP endpoint. It connects to the `db` service on the internal Docker network.

Key security features:
- `read_only: true` — Container filesystem is read-only. Only `/tmp` (tmpfs) and `/app/data` (volume) are writable.
- `cap_drop: [ALL]` — All Linux capabilities removed.
- `no-new-privileges` — Prevents privilege escalation.
- The container runs as a non-root user (`appuser`).

### Volumes

| Volume | Mount | Purpose |
|--------|-------|---------|
| `pgdata` | `/var/lib/postgresql/data` | PostgreSQL data files |
| `app_data` | `/app/data` | Auto-generated encryption key |

:::info Back Up Your Volumes
Both volumes contain critical data. Back up `pgdata` for your database and `app_data` for your encryption key. Without the encryption key, stored service credentials cannot be decrypted.
:::

### Customization

To override any default, create a `.env` file alongside `docker-compose.yml`:

**Change the host port:**

```bash
APP_PORT=9000
```

**Use an external database:**

Set `DATABASE_URL` to a full connection string:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@external-db:5432/mcp_home
```

When using an external database, you can remove the `db` service and `pgdata` volume from your compose file.

**Pin a specific version:**

Instead of `:latest`, edit the `image:` line in `docker-compose.yml` directly, or use the version-pinned compose file from a [GitHub Release](https://github.com/johnkozaris/mcpHomeManager/releases).

See the full list of configuration options in [Environment Variables](environment-variables).
