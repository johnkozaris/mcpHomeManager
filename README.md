# MCP Home Manager

[![CI](https://img.shields.io/github/actions/workflow/status/johnkozaris/mcpHomeManager/ci.yml?branch=main&label=ci)](https://github.com/johnkozaris/mcpHomeManager/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/johnkozaris/mcpHomeManager?display_name=tag)](https://github.com/johnkozaris/mcpHomeManager/releases)
[![License](https://img.shields.io/github/license/johnkozaris/mcpHomeManager)](LICENSE)
[![GHCR](https://img.shields.io/badge/ghcr-package-blue?logo=github)](https://github.com/johnkozaris/mcpHomeManager/pkgs/container/mcp-home-manager)

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
cp .env.example .env
# Edit POSTGRES_PASSWORD in .env before continuing.
# Optional: change APP_NAME for the web UI and MCP_SERVER_NAME for connected MCP clients.
docker compose up -d
```

Open <http://localhost:8000>, create your admin account, and connect services.

- MCP endpoint: `http://localhost:8000/mcp/`
- API/GUI: `http://localhost:8000/`

`APP_NAME` controls the name shown in the web UI (including the sidebar and browser title). `MCP_SERVER_NAME` controls the server name exposed to MCP clients.

## Releases and container images

- Official releases are published from semver tags like `v0.1.0`.
- Merges to `main` run CI but do **not** publish release images.
- GHCR image: `ghcr.io/johnkozaris/mcp-home-manager`
- For durable self-hosted installs, prefer the `docker-compose.yml` and `.env.example` attached to a GitHub Release instead of the files on `main`.

```bash
# Latest stable release
docker pull ghcr.io/johnkozaris/mcp-home-manager:latest

# Pin a specific release
docker pull ghcr.io/johnkozaris/mcp-home-manager:0.1.0
```

To pin a published image in Compose, set `MCP_HOME_IMAGE` in `.env` before running `docker compose up -d`:

```bash
cp .env.example .env
# Edit .env and set MCP_HOME_IMAGE=ghcr.io/johnkozaris/mcp-home-manager:0.1.0
docker compose up -d
```

GitHub Releases include the operator-facing `docker-compose.yml`, a release-pinned `.env.example`, checksums, SBOM metadata, and image-signature verification instructions for each published release.

### Upgrade notes for self-hosted installs

- Back up the Docker volumes `pgdata` and `app_data` before upgrading.
- Download the matching release assets for the version you want to deploy.
- Copy the new `.env.example` to your local `.env` only after reviewing any new settings.
- Run `docker compose pull && docker compose up -d`, then review container health/logs.

### Image pinning policy

- The **app image** is pinned by exact release tag in GitHub Release assets.
- The default Compose examples keep **PostgreSQL** on the configured major line (`postgres:17-alpine`) so patch updates remain easy, but you can override `POSTGRES_IMAGE` in `.env` if you need stricter pinning.
- The bundled Compose file assumes the included PostgreSQL service. If you want to use an external database, treat the Compose file as a starting point and adjust the services and environment accordingly.

### Verifying a published image

- Release images are keylessly signed with Cosign using GitHub Actions OIDC.
- Each GitHub Release includes `release-metadata.txt` for the pushed digest and `verify-image-signature.txt` with an exact verification command.

```bash
cosign verify \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity "https://github.com/johnkozaris/mcpHomeManager/.github/workflows/publish.yml@refs/tags/v0.1.0" \
  ghcr.io/johnkozaris/mcp-home-manager@sha256:<digest-from-release-metadata>
```

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
uv run ruff check src/
uv run mypy
npx --yes pyright
uv run python -m pytest -x -q
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
pnpm lint
pnpm build
pnpm test
```

## Localization (i18n) workflow

Frontend strings are localized with `i18next` + `react-i18next`.

- Locale files live in: `frontend/src/i18n/locales/<locale>/`
- Source language is `en`
- Namespaces are split by feature (`auth`, `dashboard`, `services`, `settings`, `components`, `errors`, `backendErrors`, etc.)

### Supported locales

`en`, `es`, `pt-BR`, `pt-PT`, `zh-CN`, `ja`, `ko`, `el`, `de`, `fr`, `th`, `it`

### Translator guidance

- Keep the same filename/key structure as `en` for every locale.
- Preserve placeholders/ICU syntax exactly (`{count}`, `{appName}`, ICU plural blocks).
- Translate with a native-speaker voice for each locale (modern product tone, not literal word-by-word).
- Keep technical loanwords (API, token, JSON, URL, MCP) when that is what native users naturally say.
- Prefer natural local phrasing over formal/stiff wording.

## Open-source docs

- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)

## License

MIT — see [LICENSE](LICENSE).
