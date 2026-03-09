## Installation

MCP Home Manager runs as two Docker containers — the application and a PostgreSQL database. The recommended setup takes about two minutes.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+ (`docker compose` — not the legacy `docker-compose`)

### Quick Start

:::steps
1. **Download the files** — Grab `docker-compose.yml` and `.env.example` from the [latest GitHub release](https://github.com/johnkozaris/mcpHomeManager/releases/latest), or clone the repository:

```bash
git clone https://github.com/johnkozaris/mcpHomeManager.git
cd mcpHomeManager
```

2. **Create your environment file** — Copy the example and set a strong database password:

```bash
cp .env.example .env
```

Edit `.env` and change `POSTGRES_PASSWORD` to a strong, unique password:

```bash
POSTGRES_PASSWORD=your-strong-password-here
```

3. **Start the stack**:

```bash
docker compose up -d
```

4. **Open the web UI** — Navigate to `http://your-server:8000` to complete [first-time setup](first-setup).
:::

### What Gets Deployed

| Container | Image | Purpose |
|-----------|-------|---------|
| `db` | `postgres:17-alpine` | PostgreSQL database |
| `app` | `ghcr.io/johnkozaris/mcp-home-manager:latest` | Application server |

| Volume | Purpose |
|--------|---------|
| `pgdata` | PostgreSQL data (service connections, users, audit logs) |
| `app_data` | Application data (auto-generated encryption key) |

The application container runs with hardened security defaults:

- **Read-only filesystem** — The container filesystem is mounted read-only
- **No new privileges** — Prevents privilege escalation
- **All capabilities dropped** — Minimal Linux capabilities
- **Non-root user** — Runs as `appuser`, not root

### Configuration

The `.env` file controls all configuration. At minimum, you need to set `POSTGRES_PASSWORD`. See [Environment Variables](environment-variables) for the full reference.

Common options you may want to change:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `8000` | Host port for the web UI and MCP endpoint |
| `PUBLIC_URL` | `http://localhost:8000` | Public-facing URL (used in password reset emails) |
| `APP_NAME` | `MCP Manager` | Branding shown in the web UI |
| `MCP_SERVER_NAME` | `My Homelab` | Name shown to MCP clients |

### Updating

Pull the latest image and recreate the container:

```bash
docker compose pull
docker compose up -d
```

Your data is stored in Docker volumes and persists across updates.

### Uninstalling

To remove the containers but keep your data:

```bash
docker compose down
```

To remove everything including data:

```bash
docker compose down -v
```
