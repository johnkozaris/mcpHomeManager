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

## Run checks before opening a PR

### Backend checks

```bash
cd backend
uv run python -m pytest -x -q
uv run python -m pytest tests/test_service_manager.py -x -q
uv run python -m pytest tests/test_service_manager.py::test_create_service -x -q
uv run ruff check src/
```

### Frontend checks

```bash
cd frontend
pnpm exec vitest run
pnpm exec vitest run src/components/ui/Badge.test.tsx
pnpm exec vitest run -t "renders children"
pnpm exec tsc -b
pnpm exec eslint .
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

## Security issues

Please do not open public issues for sensitive vulnerabilities.
Follow [SECURITY.md](SECURITY.md) for reporting instructions.

## Contribution license

By submitting a contribution, you agree that your contributions are licensed under this repository's MIT License.
