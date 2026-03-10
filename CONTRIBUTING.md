# Contributing to MCP Home Manager

Thanks for helping improve MCP Home Manager. We welcome bug fixes, security improvements, docs updates, and new service integrations.

## Prerequisites

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- Node.js 24+ with corepack enabled and pnpm
- Docker (for full-stack runs)

## Local setup

### Backend

```bash
cd backend
uv sync
uv run mcp-home          # dev server on :8000
```

### Frontend

```bash
cd frontend
corepack enable
pnpm install
pnpm dev                  # dev server on :3000, proxies /api and /mcp to :8000
```

### Full stack (Docker)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

`docker-compose.dev.yml` builds from source. It is not part of release assets.

## Run checks before opening a PR

### Backend

```bash
cd backend
uv run ruff check src/
uv run ruff format --check src/
uv run mypy
npx --yes pyright
uv run python -m pytest -x -q
```

### Frontend

```bash
cd frontend
pnpm exec tsc -b
pnpm lint
pnpm exec knip
pnpm exec vitest run
```

All of these run in CI — a PR with failures won't merge.

## Architecture

### Backend (Python / Litestar)

Ports-and-adapters layout:

```
entrypoints → services → domain ← infrastructure
```

- `domain/` — entities, ports, exceptions (framework-free)
- `services/` — business logic and orchestration
- `entrypoints/` — Litestar REST API + FastMCP server
- `infrastructure/` — persistence, HTTP clients, encryption

API schemas use `msgspec.Struct` (Pydantic is for settings only). Tests use in-memory fakes from `conftest.py` — no database needed.

### Frontend (React / Vite)

```
lib/types.ts → lib/api.ts → hooks/ → pages/ → components/
```

- TanStack Query for server state, TanStack Router for routing
- Tailwind v4 with CSS custom properties in `globals.css`
- All colors via tokens — never hardcode hex in components

## Conventions

- Use `uv` for Python, `pnpm` for frontend — no global installs
- "Connect" not "Add" when referring to services in UI copy
- `text-xs` (13px) is the minimum text size — do not use `text-2xs`
- Do not store plaintext secrets; maintain existing auth/encryption patterns
- Frontend dependency builds are locked via `pnpm-workspace.yaml` — do not widen `allowBuilds` without thorough security review

## Localization (i18n)

Frontend strings use `i18next` + `react-i18next`. Source language is `en`. Locale files: `frontend/src/i18n/locales/<locale>/`.

Supported: `en`, `es`, `pt-BR`, `pt-PT`, `zh-CN`, `ja`, `ko`, `el`, `de`, `fr`, `th`, `it`

When translating: keep ICU syntax and placeholders intact, use natural phrasing, keep technical loanwords (API, token, JSON, URL, MCP) when native speakers would.

## Pull requests

1. Branch from `main`
2. Make focused changes
3. Run the checks above
4. Open a PR explaining what changed, why, and how to test it

## Release model

Maintainers: keep versions aligned in `backend/pyproject.toml` and `frontend/package.json`, then push an annotated semver tag (`git tag -a v0.2.0 -m "Release v0.2.0" && git push origin v0.2.0`). The publish workflow handles GHCR images, cosign signing, and GitHub Release assets automatically.

## Security issues

Do not open public issues for vulnerabilities. Follow [SECURITY.md](SECURITY.md).

## License

Contributions are licensed under this repository's [MIT License](LICENSE).
