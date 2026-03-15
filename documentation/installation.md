## Installation

MCP Home Manager is a single Docker container. Pull it from GitHub Container Registry and run it.

### Option 1: Use the provided compose file

The fastest way. Clone the repo and start:

```bash
git clone https://github.com/johnkozaris/mcpHomeManager.git
cd mcpHomeManager
docker compose up -d
```

Or grab just the `docker-compose.yml` from the [latest release](https://github.com/johnkozaris/mcpHomeManager/releases/latest) and run `docker compose up -d` in the same directory.

### Option 2: Pull the image directly

If you manage your own compose files or use Portainer/Dockge/another stack manager, pull the image and configure it yourself:

```
ghcr.io/johnkozaris/mcp-home-manager:latest
```

Minimal setup:

```yaml
services:
  mcp-home-manager:
    image: ghcr.io/johnkozaris/mcp-home-manager:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - mcp_data:/app/data

volumes:
  mcp_data:
```

The container stores its SQLite database and encryption key in `/app/data`. Mount a volume there so your data survives restarts.

See [Docker Compose](docker-compose) for the full hardened configuration with read-only filesystem and dropped capabilities.

### After starting

Open `http://your-server:8000` in your browser to complete [first-time setup](first-setup).

### Updating

```bash
docker compose pull
docker compose up -d
```

Data is stored in Docker volumes and persists across updates.

### Uninstalling

Remove containers but keep data:

```bash
docker compose down
```

Remove everything including data:

```bash
docker compose down -v
```
