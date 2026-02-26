# MCP Home Manager

Self-hosted MCP gateway for homelab services. Connect Forgejo, Home Assistant, Paperless, Immich, and more to Claude, ChatGPT, or any MCP-compatible AI client.

## Quick Start

```bash
docker compose up -d
```

Visit http://localhost:8000 to get started.

## Supported Services

- Forgejo
- Home Assistant
- Paperless-ngx
- Immich
- Nextcloud
- Uptime Kuma
- AdGuard Home
- More coming soon

## Development

### Backend
```bash
cd backend
uv sync
uv run mcp-home
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## License

MIT
