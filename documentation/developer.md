## Developer Resources

MCP Home Manager is open-source. Contributions, bug reports, and feature requests are welcome.

### Getting Involved

- [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) — Dev environment setup, coding standards, PR process
- [GitHub Issues](https://github.com/johnkozaris/mcpHomeManager/issues) — Report bugs or request features
- [GitHub Releases](https://github.com/johnkozaris/mcpHomeManager/releases) — Changelog and release notes

### Architecture

```
backend/           Python 3.14, Litestar, FastMCP, SQLAlchemy, aiosqlite/asyncpg
frontend/          React 19, Vite, Tailwind v4, TanStack Query
```

:::info Hexagonal Architecture
The backend uses hexagonal architecture (also called "Ports & Adapters"). The core idea: business logic lives in the center and doesn't depend on external systems. External systems (databases, APIs, web frameworks) connect through interfaces. This makes it easy to add new service adapters without touching core logic. [Learn more](https://alistair.cockburn.us/hexagonal-architecture/)
:::

The three layers:

- **Domain** — Entities (`ServiceConnection`, `ToolDefinition`, `User`), port interfaces, business rules. No external dependencies.
- **Infrastructure** — Service client adapters (one per service type), database persistence (SQLAlchemy), credential encryption.
- **Entrypoints** — Litestar REST API (serves the web UI) and the MCP server (serves AI agents).

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
- `execute_tool(tool_name, arguments)` — Run a named tool with the given parameters
- `get_tool_definitions()` — Return available tools with JSON Schema parameter descriptions

Some adapters also implement `IAppProvider` to serve interactive HTML apps (see [MCP Apps](mcp-apps)).

### MCP Server

The MCP server (built on [FastMCP](https://github.com/jlowin/fastmcp)) handles the AI agent side.

**Dynamic instructions** — The server generates context for connected AI agents automatically. It lists available services with human-readable labels so agents know what's available without manual prompting. Instructions update whenever services change.

**Meta-tools** — When [Self-MCP](self-mcp) is enabled, management tools are registered on the MCP endpoint. Write operations (add, update, delete) require admin privileges. All meta-tools require both the global self-MCP setting and the per-user flag to be enabled.

### Key Technologies

| Component | Technology |
|-----------|-----------|
| Web framework | [Litestar](https://litestar.dev/) |
| MCP server | [FastMCP](https://github.com/jlowin/fastmcp) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite (default) or PostgreSQL (via `DATABASE_URL`) |
| Frontend | React 19 + TypeScript + Vite 6 |
| Package management | uv (Python), pnpm (Node) |

### API

The REST API serves the web UI. The OpenAPI schema is disabled in production for security. Refer to source code in `backend/src/entrypoints/api/` for endpoint details.

The MCP endpoint at `/mcp/` follows the [Model Context Protocol specification](https://modelcontextprotocol.io).

### Development Setup

See the [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) for local dev environment setup.
