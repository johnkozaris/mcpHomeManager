# MCP Home Manager

**MCP Home Manager is an open-source, self-hosted gateway that connects your homelab services to AI clients through the Model Context Protocol (MCP).**

Connect your services once in the dashboard, then use them from Claude, ChatGPT, Cursor, or any MCP-compatible client.

## What the product does

- Exposes your connected services as MCP tools
- Lets you control per-service and per-tool access
- Tracks tool calls in audit logs
- Supports one-click discovery for common Docker-hosted services
- Provides import/export for service configuration

Examples:

- “Search my Paperless documents for tax receipts”
- “Pause an Uptime Kuma monitor”
- “List open issues on my Forgejo repos”

## Quick start

```bash
git clone https://github.com/johnkozaris/mcpHomeManager.git
cd mcpHomeManager
docker compose up -d
```

Open <http://localhost:8000>, create your admin account, and connect services.

- MCP endpoint: `http://localhost:8000/mcp/`
- API/GUI: `http://localhost:8000/`

## Supported services

Built-in integrations:

- forgejo, homeassistant, paperless, immich, nextcloud, uptimekuma, adguard
- nginxproxymanager, portainer, freshrss, wallabag, stirlingpdf, wikijs
- calibreweb, tailscale, cloudflare
- generic_rest (custom tool definitions for arbitrary REST APIs)

## Connect an AI client

Use MCP Streamable HTTP with your endpoint:

`http://<your-host>:8000/mcp/`

Send your API key via `Authorization: Bearer YOUR_API_KEY`.

## Developer quick commands

### Backend

```bash
cd backend
uv sync
uv run mcp-home
uv run python -m pytest -x -q
uv run python -m pytest tests/test_service_manager.py -x -q
uv run ruff check src/
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
pnpm exec vitest run
pnpm exec vitest run src/components/ui/Badge.test.tsx
pnpm exec tsc -b
pnpm exec eslint .
```

## Open-source docs

- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)

## License

MIT — see [LICENSE](LICENSE).
