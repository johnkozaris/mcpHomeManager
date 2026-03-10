# MCP Home Manager

[![CI](https://img.shields.io/github/actions/workflow/status/johnkozaris/mcpHomeManager/ci.yml?branch=main&label=ci)](https://github.com/johnkozaris/mcpHomeManager/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/johnkozaris/mcpHomeManager?display_name=tag)](https://github.com/johnkozaris/mcpHomeManager/releases)
[![License](https://img.shields.io/github/license/johnkozaris/mcpHomeManager)](LICENSE)
[![GHCR](https://img.shields.io/badge/ghcr-package-blue?logo=github)](https://github.com/johnkozaris/mcpHomeManager/pkgs/container/mcp-home-manager)

**Self-hosted gateway that connects your homelab services to AI clients through the [Model Context Protocol](https://modelcontextprotocol.io).**

Connect your services once in the dashboard, then use them from Claude, ChatGPT, Cursor, Codex, Copilot, or any MCP-compatible client.

## What it does

- Exposes connected services as MCP tools through a single endpoint
- Per-service and per-tool access control
- Multi-user with scoped API keys and audit logs
- 17 built-in service adapters + Generic REST for anything else
- Self-management tools let your AI agent connect services without the web UI

## Quick start

```bash
git clone https://github.com/johnkozaris/mcpHomeManager.git
cd mcpHomeManager
docker compose up -d
```

Open `http://localhost:8000`, create your admin account, and connect your first service.

## Connect an AI client

Point your MCP client at:

```
http://<your-host>:8000/mcp/
```

Authenticate with `Authorization: Bearer YOUR_API_KEY`.

Works with Claude Desktop, Claude Code, Cursor, Codex, GitHub Copilot CLI, OpenCode, ChatGPT, Open WebUI, and any MCP-compatible client. See the [agent setup guides](https://mcphomemanager.com/docs#claude-desktop) for step-by-step instructions.

## Supported services

forgejo, homeassistant, paperless, immich, nextcloud, uptimekuma, adguard, nginxproxymanager, portainer, freshrss, wallabag, stirlingpdf, wikijs, calibreweb, tailscale, cloudflare, generic_rest

## Documentation

Full documentation is at **[mcphomemanager.com/docs](https://mcphomemanager.com/docs)**.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, architecture overview, and PR guidelines.

## License

MIT — see [LICENSE](LICENSE).
