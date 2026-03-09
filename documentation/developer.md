## Developer Resources

MCP Home Manager is an open-source project. Contributions, bug reports, and feature requests are welcome.

### Getting Involved

- [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) — Dev environment setup, coding standards, and PR process
- [GitHub Issues](https://github.com/johnkozaris/mcpHomeManager/issues) — Report bugs or request features
- [GitHub Releases](https://github.com/johnkozaris/mcpHomeManager/releases) — Changelog and release notes

### Architecture

```
backend/           Python 3.14, Litestar, FastMCP, SQLAlchemy, asyncpg
frontend/          React 19, Vite, Tailwind v4, TanStack Query
```

The backend follows **hexagonal architecture** (Ports & Adapters):

- **Domain layer** — Entities (`ServiceConnection`, `ToolDefinition`, `User`), ports (interfaces), and business logic
- **Infrastructure layer** — Service client adapters (one per service type), PostgreSQL persistence, encryption
- **Entrypoints** — Litestar REST API (web UI backend) and MCP server (AI agent endpoint)

### Service Adapter Structure

Each service integration is a self-contained client in `backend/src/infrastructure/clients/`:

```
base_client.py              Base class with shared HTTP, auth, error handling
homeassistant_client.py     Home Assistant adapter
paperless_client.py         Paperless-ngx adapter
...                         (17 adapters total)
```

Every adapter implements the `IServiceClient` interface:
- `health_check()` — Verify the service is reachable
- `execute_tool(tool_name, arguments)` — Run a named tool
- `get_tool_definitions()` — Return available tools with JSON Schema parameters

Some adapters also implement `IAppProvider` to serve interactive HTML apps via MCP (e.g., Home Assistant entity dashboard, Paperless document search, Forgejo repo browser).

### Key Technologies

| Component | Technology |
|-----------|-----------|
| Web framework | [Litestar](https://litestar.dev/) |
| MCP server | [FastMCP](https://github.com/jlowin/fastmcp) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (asyncpg driver) |
| Frontend | React 19 + TypeScript + Vite 6 |
| Package management | uv (Python), pnpm (Node) |

### API

The REST API serves the web UI frontend. The OpenAPI schema is not exposed via Swagger UI in production (openapi disabled). Refer to the source code in `backend/src/entrypoints/api/` for endpoint details.

The MCP endpoint at `/mcp/` follows the [Model Context Protocol specification](https://modelcontextprotocol.io).

### Development Setup

See the [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) for full instructions on setting up a local development environment.
