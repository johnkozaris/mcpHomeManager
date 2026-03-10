## Environment Variables

All configuration is set via environment variables. The `docker-compose.yml` includes sensible defaults for every variable — no `.env` file is required. To customise, create a `.env` file alongside `docker-compose.yml` and override only what you need.

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `8000` | Host port for the web UI and MCP endpoint |
| `PUBLIC_URL` | `http://localhost:8000` | Public-facing URL of the application. Used in password reset emails and the web UI. |
| `APP_NAME` | `MCP Manager` | Branding shown in the browser title, login/setup screens, and sidebar |
| `MCP_SERVER_NAME` | `My Homelab` | Name reported to MCP clients when they connect |
| `DEBUG` | `false` | Enable debug logging |
| `SELF_MCP_ENABLED` | `true` | Expose [self-management tools](self-mcp) via the MCP endpoint |
| `HEALTH_CHECK_INTERVAL_SECONDS` | `60` | How often to check connected service health (seconds) |
| `HTTP_TIMEOUT_SECONDS` | `30` | Timeout for HTTP requests to connected services |

### Database

The default database is SQLite — zero configuration required. All data is stored in the `app_data` volume. To use PostgreSQL instead, set `DATABASE_URL` or use the `docker-compose.postgres.yml` override file.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite (auto) | Full database connection string. For PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `POSTGRES_PASSWORD` | — | When set (without `DATABASE_URL`), builds a PostgreSQL URL from the `POSTGRES_*` variables below |
| `POSTGRES_HOST` | `db` | PostgreSQL host (only used when `POSTGRES_PASSWORD` is set) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `mcp_home` | PostgreSQL database name |
| `POSTGRES_USER` | `mcp` | PostgreSQL username |

### Auto-Generated

| Variable | Description |
|----------|-------------|
| `ENCRYPTION_KEY` | Fernet encryption key used to encrypt service credentials at rest. **Auto-generated on first start** and saved to `/app/data/encryption_key`. |

:::info Do Not Change ENCRYPTION_KEY After Setup
The encryption key is generated automatically the first time MCP Home Manager starts. It is persisted in the `app_data` Docker volume. If you lose this key or change it, all stored service credentials become unreadable and must be re-entered.

You can set `ENCRYPTION_KEY` as an environment variable to use a specific key (e.g., when restoring from backup). If set, it takes precedence over the file in `/app/data/`.
:::

### Example `.env` File

```bash
# Optional — override only what you need.
# APP_PORT=9000
# PUBLIC_URL=https://mcp.example.com
# APP_NAME=My MCP Manager
# MCP_SERVER_NAME=My Homelab
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```
