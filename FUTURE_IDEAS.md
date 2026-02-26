# Future Ideas

Roadmap and ideas for MCP Home Manager. This project aims to be the universal MCP gateway for self-hosted homelabs — not just one person's setup.

---

## Implemented Features

The following features have been completed and are part of the current codebase:

| Feature | Status | Details |
|---------|--------|---------|
| Service Discovery | Done | Docker socket inspection via `aiodocker` |
| Model & Client Tracking | Done | `client_name` captured in audit logs, displayed in Logs UI |
| Permission Profiles | Done | Read-only / Contributor / Admin profiles per service type |
| Observability | Done | Prometheus `/metrics` endpoint + structlog JSON logging |
| Self-MCP Meta-Tools | Done | 5 management tools exposed via MCP protocol |
| YAML Config Export/Import | Done | Export/import service configs as YAML files |
| Monaco Editor | Done | Embedded code editor for JSON config editing |
| Terminal Code Blocks | Done | Mac-style terminal chrome for all code examples |
| Confirm Dialogs | Done | Accessible modal dialogs replacing native `confirm()` |
| Alembic Migrations | Done | Database schema version control |
| 7 Service Integrations | Done | Forgejo, Home Assistant, Paperless, Immich, Nextcloud, Uptime Kuma, AdGuard |
| OAuth 2.1 MCP Auth | Done | Multi-mode auth (none/api_key/oauth), JWT verification, RFC 9728 metadata |
| Multi-User Support | Done | Togglable per-user API keys, service-level access control, admin roles |
| Generic REST Adapter | Done | Custom REST APIs as MCP tools, OpenAPI 3.x import |
| Docker Deployment | Done | Zero-config `docker compose up -d` with auto-generated secrets |
| MCP Apps Phase 1 | Done | 3 HTML UI tools (dashboard, service control, config) via Jinja2 templates |
| MCP Apps Phase 2/3 | Done | Per-service interactive apps (HA entities, Paperless search, Forgejo repos), write-back actions via postMessage |
| Plugin System | Removed | Was over-engineered for current needs; custom tools on any service type covers the use case |

---

## Semi-Opinionated + Dynamic Service Support

**Opinionated for known services, flexible for everything else:**

- **Known services** (Forgejo, HA, Paperless, Immich, Nextcloud, etc.) get:
  - Pre-built tool definitions with proper parameter schemas
  - Health check implementations
  - Recommended permission profiles
  - Logo/icon in the UI
- **Unknown services** can be added dynamically:
  - User provides base URL + API token
  - Option to paste an OpenAPI/Swagger spec → auto-generate tools
  - Manual tool definition via the UI (name, description, HTTP method, path, params)
  - "Generic REST" adapter that wraps any REST endpoint as an MCP tool

## Additional Service Integrations

**Expand beyond the initial seven:**

| Service | Status | Notes |
|---------|--------|-------|
| Nginx Proxy Manager | Planned | Proxy host management |
| Actual Budget | Planned | Financial queries, transaction search |
| Wiki.js | Planned | Page CRUD, search documentation |
| AFFiNE | Planned | Workspace management, document operations |
| Cloudflare | Planned | Tunnel management, DNS records |
| Tailscale | Planned | Device management, ACLs |
| Stirling PDF | Planned | PDF operations (merge, split, OCR) |
| Calibre Web | Planned | E-book search and metadata |
| FreshRSS | Planned | Feed management, article search |

---

## Future TODOs (Large)

These features are significant undertakings deferred to future development cycles:

### Webhook / Event-Driven Integration

- Listen for webhooks from services (Forgejo push events, HA state changes)
- Surface events to the LLM client via MCP notifications
- Enable proactive alerts: "Your front door was unlocked" → LLM can take action

### MCP Apps (Interactive UI in Chat) — Phase 1 IMPLEMENTED (Sprint 3)

Phase 1 (template infrastructure + 3 HTML UI tools) implemented. See:
- `backend/src/entrypoints/mcp/template_engine.py` — Jinja2 renderer
- `backend/src/entrypoints/mcp/templates/` — base, dashboard, control, config templates
- `backend/src/entrypoints/mcp/meta_tools.py` — 3 UI tools registered alongside 5 existing meta-tools

#### Remaining Phases — IMPLEMENTED
2. Per-service interactive apps: HA entity dashboard, Paperless document search, Forgejo repo browser
3. Write-back actions via iframe postMessage + `handle_app_action()` callback

### Plugin System — REMOVED

Removed in favor of custom tool definitions on any service type. Users can add custom REST endpoints to any built-in service via "Add Tool" or "Import OpenAPI" on the service detail page.

### Multi-User Support — IMPLEMENTED (Sprint 2)

See `backend/src/services/user_service.py` and `frontend/src/pages/Users.tsx`.

### Deployment Features

- One-click Ansible stack for homelab deployment
- Helm chart for Kubernetes
- Automatic HTTPS via reverse proxy
