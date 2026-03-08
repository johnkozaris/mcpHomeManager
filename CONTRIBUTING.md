# Contributing to MCP Home Manager

Thanks for helping improve MCP Home Manager.

This project is an open-source MCP gateway for homelab services, and we welcome bug fixes, security improvements, docs updates, and new service integrations.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Node.js 24+ with corepack enabled
- pnpm
- Docker (recommended for local full-stack runs)

## Local setup

### Backend

```bash
cd backend
uv sync
uv run mcp-home
```

### Frontend

```bash
cd frontend
corepack enable
pnpm install
pnpm dev
```

### Docker / full stack

```bash
cp .env.example .env
# Set a strong POSTGRES_PASSWORD before first start
docker compose up -d
```

For contributor workflows, `docker-compose.dev.yml` is a local override for source builds. It is not part of the GitHub Release asset bundle.

## Run checks before opening a PR

### Backend checks

```bash
cd backend
uv run ruff check src/
uv run mypy
npx --yes pyright
uv run python -m pytest -x -q
```

### Frontend checks

```bash
cd frontend
pnpm lint
pnpm build
pnpm test
```

## What to know about this codebase

### Backend structure

The backend uses a ports-and-adapters layout:

`entrypoints -> services -> domain <- infrastructure`

- `domain/`: entities, ports, exceptions (framework-free)
- `services/`: business/use-case orchestration
- `entrypoints/`: Litestar API + MCP mount
- `infrastructure/`: persistence, external clients, encryption, metrics

### Frontend structure

Primary flow:

`lib/types.ts -> lib/api.ts -> hooks/useServices.ts -> pages -> components`

- TanStack Query is the source of truth for server state
- TanStack Router route definitions are in `src/routeTree.tsx`

## Project conventions

- Use `uv` for Python workflows and `pnpm` for frontend workflows.
- API schemas are `msgspec.Struct` (Pydantic is for settings only).
- Backend tests should use in-memory fakes from `backend/tests/conftest.py`.
- Use “Connect” wording in UX copy for services.
- Keep UI colors token-based (`frontend/src/styles/globals.css`), not hardcoded per component.
- Do not store plaintext secrets; keep existing auth/encryption patterns intact.

## Pull requests

1. Create a feature branch from `main`
2. Make focused changes
3. Run relevant checks above
4. Open a PR with:
   - what changed
   - why it changed
   - how to test it

## Release model

If you're maintaining releases, keep `backend/pyproject.toml` and `frontend/package.json` aligned, then push an annotated semver tag from `main` (for example `git tag -a v0.1.0 -m "Release v0.1.0"` followed by `git push origin v0.1.0`). The publish workflow handles GHCR publishing and GitHub Release assets automatically; after it finishes, verify the release page before announcing it.

## Security issues

Please do not open public issues for sensitive vulnerabilities.
Follow [SECURITY.md](SECURITY.md) for reporting instructions.

## Contribution license

By submitting a contribution, you agree that your contributions are licensed under this repository's MIT License.
