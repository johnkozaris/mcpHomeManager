## Overview

MCP Home Manager is a self-hosted gateway that connects your homelab services to AI agents via the [Model Context Protocol](https://modelcontextprotocol.io). One Docker container, one endpoint, every service.

### How It Works

:::steps
1. **Deploy** — Run the Docker container on your homelab
2. **Connect services** — Add your services through the web UI (URL + credentials)
3. **Point your AI** — Configure your AI agent to use `http://your-server:8000/mcp/`
:::

Your AI agent can then interact with all connected services through conversation — control Home Assistant devices, search Paperless-ngx documents, browse Immich photos, manage Forgejo repos, and more.

### What makes it different

- **One endpoint** — Your AI agent connects once, talks to everything
- **17 built-in adapters** — Native support for popular homelab services
- **Generic REST + OpenAPI import** — Connect any service with an API
- **Self-MCP** — Your AI agent can add services, toggle tools, and manage the hub itself. No web UI needed.
- **Multi-user** — Each user gets their own API key, service access, and audit trail
- **Self-hosted** — Your data stays on your hardware

### Supported Services

| Service | Description |
|---------|-------------|
| [Home Assistant](home-assistant) | Smart home control |
| [Paperless-ngx](paperless-ngx) | Document management |
| [Immich](immich) | Photo library |
| [Forgejo](forgejo) | Git hosting |
| [Uptime Kuma](uptime-kuma) | Service monitoring |
| [Nextcloud](nextcloud) | Files and notes |
| [AdGuard Home](adguard) | DNS filtering |
| [Portainer](portainer) | Container management |
| [Nginx Proxy Manager](nginx-proxy-manager) | Reverse proxy |
| [FreshRSS](freshrss) | RSS reader |
| [Wallabag](wallabag) | Read-it-later |
| [Calibre-Web](calibre-web) | Ebook library |
| [Wiki.js](wikijs) | Wiki |
| [Tailscale](tailscale) | VPN management |
| [Cloudflare](cloudflare) | DNS and tunnels |
| [Stirling PDF](stirling-pdf) | PDF tools |
| [Generic REST](generic-rest) | Any REST API |

### Supported AI Agents

[Claude Desktop](claude-desktop) · [Claude Code](claude-code) · [Cursor](cursor) · [Codex](codex) · [GitHub Copilot CLI](copilot-cli) · [OpenCode](opencode) · [ChatGPT](chatgpt)

### Next Steps

Ready to deploy? Go to [Installation](installation).
