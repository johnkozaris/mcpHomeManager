## Environment Variables

All configuration is set via environment variables in the `.env` file. Copy `.env.example` to `.env` before starting MCP Home Manager.

### Required

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | — | Password for the PostgreSQL database. **Must be set.** |
| `MCP_HOME_IMAGE` | — | Docker image for the application. Set in `.env.example`. |

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

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `mcp_home` | PostgreSQL database name |
| `POSTGRES_USER` | `mcp` | PostgreSQL username |
| `POSTGRES_PASSWORD` | — | PostgreSQL password (**required**) |
| `POSTGRES_IMAGE` | `postgres:17-alpine` | PostgreSQL Docker image |
| `DATABASE_URL` | — | Full connection string. Overrides individual `POSTGRES_*` variables. Format: `postgresql+asyncpg://user:pass@host:5432/dbname` |

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
# Application
APP_PORT=8000
PUBLIC_URL=http://localhost:8000
APP_NAME=MCP Manager
MCP_SERVER_NAME=My Homelab

# Image
MCP_HOME_IMAGE=ghcr.io/johnkozaris/mcp-home-manager:latest

# Database
POSTGRES_IMAGE=postgres:17-alpine
POSTGRES_DB=mcp_home
POSTGRES_USER=mcp
POSTGRES_PASSWORD=change-this-strong-password
```
