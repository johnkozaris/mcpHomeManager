## Overview

MCP Home Manager is a self-hosted gateway that connects your homelab services to AI agents via the [Model Context Protocol](https://modelcontextprotocol.io). Deploy it with Docker, connect your services, and point your AI agent at a single endpoint.

One MCP endpoint gives your AI agent structured access to every connected service — no per-service configuration, no custom plugins, no prompt hacking.

:::info Why MCP Home Manager?
- **One endpoint** — Your AI agent connects once, accesses everything
- **17 built-in adapters** — Native support for popular homelab services
- **Multi-user** — Each user gets their own API key, service access, and audit trail
- **Self-hosted** — Your data stays on your hardware, encrypted at rest
- **Extensible** — Connect any REST API with the Generic REST adapter or OpenAPI import
:::

### How It Works

:::steps
1. **Deploy** — Run `docker compose up -d` to start MCP Home Manager and PostgreSQL
2. **Connect services** — Add your homelab services through the web UI (URL + credentials)
3. **Point your AI agent** — Configure Claude Desktop, Claude Code, Cursor, or another MCP client to use your endpoint at `http://your-server:8000/mcp/`
:::

Your AI agent can then interact with all your connected services through natural conversation — query your Home Assistant entities, search Paperless-ngx documents, browse Immich photos, manage Forgejo repositories, and more.

### Supported Services

| Service | Tools | Description |
|---------|-------|-------------|
| [Home Assistant](home-assistant) | 4 | Smart home control and entity state |
| [Paperless-ngx](paperless-ngx) | 5 | Document search and metadata |
| [Immich](immich) | 5 | Photo search and album browsing |
| [Forgejo](forgejo) | 7 | Git repositories, issues, and pull requests |
| [Uptime Kuma](uptime-kuma) | 4 | Monitor status and control |
| [Nextcloud](nextcloud) | 5 | Files and notes |
| [AdGuard Home](adguard) | 6 | DNS filtering status and logs |
| [Portainer](portainer) | 8 | Container management |
| [Nginx Proxy Manager](nginx-proxy-manager) | 7 | Reverse proxy host management |
| [FreshRSS](freshrss) | 7 | RSS feed reading |
| [Wallabag](wallabag) | 7 | Read-it-later article management |
| [Calibre-Web](calibre-web) | 5 | E-book library browsing |
| [Wiki.js](wikijs) | 6 | Wiki page management |
| [Tailscale](tailscale) | 5 | VPN device and DNS management |
| [Cloudflare](cloudflare) | 5 | DNS records and tunnel management |
| [Stirling PDF](stirling-pdf) | 2 | PDF service status |
| [Generic REST](generic-rest) | Custom | Connect any REST API |

### Supported AI Agents

- [Claude Desktop](claude-desktop) — Full MCP support with interactive apps
- [Claude Code](claude-code) — CLI-based MCP integration
- [Cursor](cursor) — IDE with MCP support
- [Codex](codex) — OpenAI's coding agent (CLI + desktop)
- [GitHub Copilot CLI](copilot-cli) — GitHub's terminal agent
- [OpenCode](opencode) — Open-source terminal agent
- [ChatGPT](chatgpt) — Requires publicly accessible HTTPS endpoint

### Requirements

- Docker and Docker Compose v2+
- 128 MB RAM minimum
- Network access to your homelab services

### Next Steps

Ready to get started? Head to the [Installation](installation) guide.
